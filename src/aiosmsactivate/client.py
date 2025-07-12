import asyncio
import json
import logging
import re
import time
from typing import Any, Literal
from async_lru import alru_cache

import aiohttp

from .utils import is_json
from .exceptions import SmsActivateException, raise_smsactivate_error
from .models import ActivationData, Number, Service, SetActivationStatusResponse, Sms
from .types import SetActivationStatus, ActivationStatus

__all__ = [
    "SmsActivate",
]


allowed_domains = [
    'https://api.sms-activate.ae/stubs/handler_api.php',
    'https://api.sms-activate.ru/stubs/handler_api.php',
    'https://api.sms-activate.io/stubs/handler_api.php',
    'https://api.sms-activate.page/stubs/handler_api.php',
]

class SmsActivate:
    """
    RU  
    Спасибо за использование моей библиотеки, вы можете принять участие в развитии библиотеки  
      
    ВАЖНО
    библиотека полностью поддерживает все методы с оффициальной документации
    https://sms-activate.page/api2 на момент 08.07.2025  
      
    на git: https://github.com/AioSmsProviders/aiosmsactivate
    Так же можете писать в чат https://t.me/+5YQ8k6H02bkxZmRi
    или обратиться к главному разработчику с идеями, предложениями и багами: https://t.me/lolkof  
    
    EN  
    Thank you for using my library, you can participate in the development of the library.  
      
    important
    The library fully supports all methods from the official documentation
    https://sms-activate.page/api2 as of 07/08/2025  
      
    on git: https://github.com/AioSmsProviders/aiosmsactivate
    You can also write to the chat https://t.me/+5YQ8k6H02bkxZmRi
    or contact the main developer with ideas, suggestions, and bugs: https://t.me/lolkof
    
    SIMPLE USAGE
    ```python
    from aiosmsactivate import SmsActivate
    from aiosmsactivate.types import SetActivationStatus

    import asyncio


    sa = SmsActivate('token')

    async def main():
        balance = await sa.get_balance()
        print(balance) # 6.25
        
        number = await sa.purchase('ya')
        number.activation_id # 3807035855
        number.phone_number # '79238944456'
        number.operator # 'mtt'
        print(number)
        # activation_id=3809954454 phone_number='79927146212' activation_cost=0.2 
        # country_code='0' can_get_another_sms=True activation_time='2025-07-09 01:14:45' 
        # operator='mtt' activation_unix_time=1654093857
        
        code = await number.wait_sms_code(timeout=300)
        print(code) # 1234
        
        status = await number.get_activation_status()
        
        await number.set_activation_status(SetActivationStatus.CANCEL) # Отменить номер || Cancel number
        await number.set_activation_status(8) # Отменить номер || Cancel number
        
    asyncio.run(main())
    ```
    """

    def __init__(self, api_key: str, base_url: str | list = allowed_domains):
        """
        RU  
        api_key передавать api ключ, получить можно вот тут: https://sms-activate.page/profile
        В base_url можно указать список адресов, модуль будет проходиться по всем, пока не найдёт рабочий
        а можно указать один или вообще не указывать, если не указать будет браться из allowed_domains  
        
        EN  
        api_key to transfer the api key, you can get it here: https://sms-activate.page/profile
        You can specify a list of addresses in base_url, and the module will go through all of them until it finds a working one.
        or you can specify one or not at all, if not specified, it will be taken from allowed_domains.
        """
        self._api_key = api_key
        if isinstance(base_url, str):
            base_url = [base_url]
        self._base_urls = base_url
        self._accept_url = None

    async def __send_request(self, action: str, **kwargs):
        last_exception = None

        for url in self._base_urls:
            try:
                url = self._accept_url if self._accept_url else url
                params = None
                if 'params' in kwargs.keys():
                    params = kwargs.pop('params')
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        'POST',
                        url,
                        **kwargs,
                        params={
                            'api_key': self._api_key,
                            'action': action,
                            **(params if params else {})
                        }
                    ) as response:
                        response.raise_for_status()
                        resp_text = await response.text()
                        raise_smsactivate_error(resp_text)
                        logging.debug(response.real_url)
                        return resp_text
            except Exception as e:
                last_exception = e
                continue
            self._accept_url = url
            break

        raise last_exception

    async def get_balance(self, cashback: bool = False) -> float:
        response = await self.__send_request('getBalance' if not cashback else 'getBalanceAndCashBack')
        data = response.split(':')
        if data[0] != 'ACCESS_BALANCE':
            raise SmsActivateException(code='SmsActivateExcetion', message='Invalid response sequence')

        return float(data[1])
    
    async def get_balance_and_cashback(self):
        return await self.get_balance(cashback=True)

    async def get_available_countries(self, service: str, freePrice: bool | str | None = None) -> dict[str, Any]:
        response = await self.__send_request('getTopCountriesByService', params={
            'service': service,
            **({'freePrice': str(freePrice).lower()} if freePrice else {})
        })
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_count_numbers(self, country: str, operator: str) -> dict[str, Any]:
        response = await self.__send_request('getNumbersStatus', params={
            'country': country,
            'operator': operator
        })
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    
    @alru_cache(maxsize=32, ttl=3600*2)
    async def get_operators(self, country: str = None) -> dict[str, Any]:
        params = {}
        if country is not None:
            params["country"] = country
        response = await self.__send_request('getOperators', params=params)
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_active_activations(self) -> dict[str, Any]:
        response = await self.__send_request('getActiveActivations')
        
        if not is_json(response):
            return response
        
        return json.loads(response)

    async def get_activation_status_v1(self, id: str) -> tuple[ActivationStatus, str | None]:
        response = await self.__send_request('getStatus', params={
            'id': id
        })

        data = response.split(':')

        match data[0]:
            case 'STATUS_WAIT_CODE':
                return ActivationStatus.WAIT, None
            case 'STATUS_WAIT_RETRY':
                return ActivationStatus.RETRY, data[1]
            case 'STATUS_WAIT_RESEND':
                return ActivationStatus.RESEND, None
            case 'STATUS_CANCEL':
                return ActivationStatus.CANCEL, None
            case 'STATUS_OK':
                return ActivationStatus.OK, data[1]
            case _:
                raise SmsActivateException('Invalid response sequence')
    
    async def get_activation_status(self, activation_id: str | int | Number) -> ActivationData | str:
        if isinstance(activation_id, Number):
            activation_id = activation_id.activation_id
        response = await self.__send_request('getStatusV2', params={
            'id': activation_id
        })

        if not is_json(response):
            return response
        
        return ActivationData(**json.loads(response))
    
    async def wait_sms_code(self, activation_id: str | int | Number, timeout: int = 60*5, per_attempt: int = 5) -> Sms | str | int | None:
        """
        Ожидание смс кода
        Wait sms code

        Аргументы:
            activation_id: activation_id номера или целый объект номера
            timeout: максимальное время ожидание смс в секундах, по умолчанию 5 минут 
            per_attempt: время между попыткой получить смс, по умолчанию 5 секунд
            
        Args:
            activation_id: activation_id of number or Number object
            timeout: maximum time to wait sms code 
            per_attempt: time per attempt
            
        Returns: Sms
        """
        activation_id = activation_id.activation_id if isinstance(activation_id, Number) else activation_id
        if not self._api_key:
            raise ValueError('API key is required for this method')

        try:
            await self.set_activation_status(activation_id=activation_id, status=SetActivationStatus.READY)
        except:
            pass

        start_time = time.time()
        
        while time.time() - start_time < timeout:
            await asyncio.sleep(per_attempt)
            status, code = await self.get_activation_status_v1(activation_id)
            if status == ActivationStatus.OK:
                try:
                    await self.set_activation_status(activation_id, SetActivationStatus.AGAIN)
                except:
                    pass
                return code
        
        return None

    async def purchase(self, service: str, forward: bool | None = None, maxPrice: float | None = None,
                       phoneException: str | None = None, operator: str | None = None,
                       activationType: int | str | None = None, language: str | None = None,
                       userId: str | int | None = None,
                       ref: str | None = None, country: str | None = None,
                       useCashBack: bool | None = None,
                       orderId: str | int | None = None,
                       _is_v2: bool = True
                       ) -> Number | str:
        response = await self.__send_request('getNumber' if not _is_v2 else 'getNumberV2', params={
            'service': service,
            **({'forward': 1 if forward else 0} if forward is not None else {}),
            **({'maxPrice': str(maxPrice)} if maxPrice is not None else {}),
            **({'phoneException': phoneException} if phoneException is not None else {}),
            **({'operator': operator} if operator is not None else {}),
            **({'activationType': str(activationType)} if activationType is not None else {}),
            **({'language': str(language)} if language is not None else {}),
            **({'userId': str(userId)} if userId is not None else {}),
            **({'orderId': str(orderId)} if orderId is not None and _is_v2 else {}),
            **({'ref': ref} if ref is not None else {}),
            **({'country ': country} if country is not None else {}),
            **({'useCashBack': str(useCashBack).lower()} if useCashBack is not None else {}),
        })

        if not is_json(response):
            return response
        
        data = json.loads(response)
        data['service'] = service
        return Number.from_response(self, data)
    
    async def get_number(self, *args, **kwargs):
        kwargs["_is_v2"] = False
        return await self.purchase(*args, **kwargs)
    
    async def get_multi_service_number(self, 
                        multiService: str, multiForward: str | None = None,
                        operator: str | None = None,
                        ref: str | None = None, country: str | None = None,
                       ) -> dict:
        """
        Get multiservice number.

        :param multiService: service1,service2,service3 (Services separated by commas)
        :param multiForward: 1,0,1 (forwards separated by commas, forwards count equal services count)
        :return: dict object of response
        """
        response = await self.__send_request('getMultiServiceNumber', params={
            'multiService': multiService,
            **({'multiForward': multiForward} if multiForward is not None else {}),
            **({'operator': operator} if operator is not None else {}),
            **({'ref': ref} if ref is not None else {}),
            **({'country ': country} if country is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    

    async def set_activation_status(self, activation_id: str | int, status: SetActivationStatus | int,
                                    forward: str | None = None) -> SetActivationStatusResponse:
        members = {member.value: member for member in SetActivationStatusResponse}
        response = await self.__send_request('setStatus', params={
            'id': activation_id,
            'status': status.value if isinstance(status, SetActivationStatus) else status,
            **({'forward': forward} if forward is not None else {})
        })

        return members[response]

    async def get_history(self, 
                          start: str | int = None,
                          end: str | int = None,
                          offset: str | int = None,
                          limit: str | int = None,
                       ) -> dict | list:
        response = await self.__send_request('getHistory', params={
            **({'start': str(start)} if start is not None else {}),
            **({'end': str(end)} if end is not None else {}),
            **({'offset': str(offset)} if offset is not None else {}),
            **({'limit': str(limit)} if limit is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_list_top_countries(self, 
                          service: str,
                       ) -> dict | list:
        response = await self.__send_request('getListOfTopCountriesByService', params={
            'service': service
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_incoming_call_status(self, 
                          id: str | int = None,
                       ) -> dict | list:
        response = await self.__send_request('getIncomingCallStatus', params={
            'activationId': id
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_service(self, service_code: str, country: str | int, lang: Literal['ru', 'en', 'es', 'cn'] = 'en') -> Service:
        """
        RU  
        Получить все данные о сервисе  
        EN  
        Get all data about service  
        
        Example
        ```python
        service = await sa.get_service('ya', 0)
        print(service)
        # code='ya' name='Yandex/Uber' country='0' 
        # price=0.115 retail_price=0.2 free_price_map={'0.3067': 17134, '0.3065': 16996, ...} 
        # count=11049 physical_count=5334
        ```
        """
        
        country = str(country)
        name = await self.get_service_name(service_code, lang)
        data = await self.get_prices(service_code, country)
        price_data = await self.get_available_countries(service_code, freePrice=True)
        price_data = price_data[country]
        
        retail_price = price_data['retail_price']
        free_price_map = price_data['freePriceMap']
        
        price = data[country][service_code]['cost']
        count = data[country][service_code]['count']
        physical_count = data[country][service_code]['physicalCount']
        return Service(
            code=service_code,
            country=country,
            name=name,
            price=price,
            retail_price=retail_price,
            count=count,
            physical_count=physical_count,
            free_price_map=free_price_map,
        )
    
    async def get_prices(self, 
                          service: str = None,
                          country: str | int = None,
                       ) -> dict | list:
        response = await self.__send_request('getPrices', params={
            **({'service': str(service)} if service is not None else {}),
            **({'country': str(country)} if country is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def _get_service_cost(self, service: str, country: str | int):
        data = await self.get_prices(service, country)
        return data[country][service]['cost']
    
    async def _get_service_quantity(self, service: str, country: str | int):
        data = await self.get_prices(service, country)
        return data[country][service]['count']
    
    async def get_prices_verification(self, 
                          service: str = None,
                       ) -> dict | list:
        response = await self.__send_request('getPricesVerification', params={
            **({'service': str(service)} if service is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_countries(self,
                       ) -> dict | list:
        response = await self.__send_request('getCountries', params={
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    @alru_cache(maxsize=32, ttl=3600*2)
    async def get_service_list(self, 
                          country: str = None,
                          lang: Literal['ru', 'en', 'es', 'cn'] = None,
                       ) -> dict | list:
        response = await self.__send_request('getServicesList', params={
            **({'country': str(country)} if country is not None else {}),
            **({'lang': str(lang)} if lang is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_service_name(self, service_code: str, lang: Literal['ru', 'en', 'es', 'cn'] = None):
        """
        RU  
        Получение полного имени сервиса по его id  
          
        EN  
        Get full service name by service code  
            
        Пример Example:  
        service_name = await SmsActivate.get_service_name('go')  
        service_name # 'Google,youtube,Gmail'
        """
        services = await self.get_service_list(lang=lang)
        services = services.get('services')
        for service in services:
            if service['code'] == service_code:
                return service['name']
        return None
    
    async def get_additional_service(self, 
                          service: str = None,
                          id: str = None,
                       ):
        """
        Get additional service to activation its cost 5rub
        return 2 values: addition activation id and phone number
        
        use like this: 
        activation_id, phone_number = await getAdditionalService(service, activation id)
        """
        response = await self.__send_request('getAdditionalService', params={
            'service': service,
            'id':id
        })

        data = response.split(':')
        if len(data) > 2:
            return data[1], data[2]
        
        return data
    
    async def get_extra_activation(self, 
                          id: str = None,
                       ):
        """
        return 2 values: addition activation id and phone number
        
        use like this: 
        activation_id, phone_number = await getExtraActivation(activation id)
        """
        response = await self.__send_request('getExtraActivation', params={
            'id':id
        })

        data = response.split(':')
        if len(data) > 2:
            return data[1], data[2]
        
        return data
    
    async def check_extra_activation(self, 
                          activationId: str | int
                       ) -> dict | list:
        response = await self.__send_request('checkExtraActivation', params={
            'activationId': str(activationId)
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def parse_call(self, 
                          id: str | int,
                          newLang: str,
                       ) -> dict | list:
        response = await self.__send_request('parseCall', params={
            "id": id,
            "newLang": newLang,
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    # !!! BOTTOM IT IS RENT API
    async def get_rent_services_and_countries(self,
                       time: int | str | None = None,
                       operator: str | None = None,
                       country: str | None = None,
                       currency: str | None = None,
                       incomingCall: bool | None = None,
                       ) -> dict | str:
        response = await self.__send_request('getRentServicesAndCountries', params={
            **({'time ': str(time )} if time is not None else {}),
            **({'operator ': str(operator )} if operator is not None else {}),
            **({'country ': str(country )} if country is not None else {}),
            **({'currency ': str(currency )} if currency is not None else {}),
            **({'incomingCall': str(incomingCall).lower()} if incomingCall is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_rent_number(self,
                        service: str,
                        time: int | str | None = None,
                        operator: str | None = None,
                        country: str | None = None,
                        url: str | None = None,
                        incomingCall: bool | None = None,
                       ) -> dict | str:
        response = await self.__send_request('getRentNumber', params={
            'service': service,
            **({'time ': str(time )} if time is not None else {}),
            **({'operator ': str(operator )} if operator is not None else {}),
            **({'country ': str(country )} if country is not None else {}),
            **({'url ': str(url )} if url is not None else {}),
            **({'incomingCall': str(incomingCall).lower()} if incomingCall is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_rent_status(self,
                        id: str,
                        page: int | str | None = None,
                        size: int | str | None = None,
                       ) -> dict | str:
        response = await self.__send_request('getRentStatus', params={
            'id': id,
            **({'page ': str(page)} if page is not None else {}),
            **({'size ': str(size )} if size is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def set_rent_status(self,
                        id: str,
                        status: Literal[1, 2, '1', '2'],
                       ) -> dict | str:
        response = await self.__send_request('getRentStatus', params={
            'id': str(id),
            'status': str(status),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_rent_list(self,
                       ) -> dict | str:
        response = await self.__send_request('getRentList', params={
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def continue_rent_number(self,
                        id: str,
                        rent_time: int | str | None = 4,
                       ) -> dict | str:
        response = await self.__send_request('continueRentNumber', params={
            'id': id,
            'rent_time': str(rent_time)
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    async def get_continue_rent_price_number(self,
                        id: str,
                        rent_time: int | str | None = 4,
                        currency: str | None = None
                       ) -> dict | str:
        response = await self.__send_request('getContinueRentPriceNumber', params={
            'id': id,
            'rent_time': str(rent_time),
            **({'currency ': str(currency )} if currency is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    
    # !!! BOTTOM IS IT PARTNER SOFT API
    async def buy_partner_product(self,
                        id: str,
                       ) -> dict | str:
        response = await self.__send_request('buyPartnerProduct', params={
            'id': id,
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    

# === Method Aliases (outside class for pdoc) ===
SmsActivate.getBalance = SmsActivate.get_balance
SmsActivate.getBalanceAndCashBack = SmsActivate.get_balance_and_cashback
SmsActivate.getTopCountriesByService = SmsActivate.get_available_countries
SmsActivate.getNumbersStatus = SmsActivate.get_count_numbers
SmsActivate.getOperators = SmsActivate.get_operators
SmsActivate.getActiveActivations = SmsActivate.get_active_activations
SmsActivate.getStatus = SmsActivate.get_activation_status_v1
SmsActivate.getStatusV2 = SmsActivate.get_activation_status
SmsActivate.getNumberV2 = SmsActivate.purchase
SmsActivate.purchase_v1 = SmsActivate.get_number
SmsActivate.getNumber = SmsActivate.get_number
SmsActivate.getMultiServiceNumber = SmsActivate.get_multi_service_number
SmsActivate.setStatus = SmsActivate.set_activation_status
SmsActivate.getHistory = SmsActivate.get_history
SmsActivate.getListOfTopCountriesByService = SmsActivate.get_list_top_countries
SmsActivate.getIncomingCallStatus = SmsActivate.get_incoming_call_status
SmsActivate.getPrices = SmsActivate.get_prices
SmsActivate.getPricesVerification = SmsActivate.get_prices_verification
SmsActivate.getCountries = SmsActivate.get_countries
SmsActivate.getServicesList = SmsActivate.get_service_list
SmsActivate.getAdditionalService = SmsActivate.get_additional_service
SmsActivate.getExtraActivation = SmsActivate.get_extra_activation
SmsActivate.checkExtraActivation = SmsActivate.check_extra_activation
SmsActivate.parseCall = SmsActivate.parse_call
SmsActivate.getRentServicesAndCountries = SmsActivate.get_rent_services_and_countries
SmsActivate.getRentNumber = SmsActivate.get_rent_number
SmsActivate.getRentStatus = SmsActivate.get_rent_status
SmsActivate.getRentStatus = SmsActivate.get_rent_status
SmsActivate.getRentList = SmsActivate.get_rent_list
SmsActivate.continueRentNumber = SmsActivate.continue_rent_number
SmsActivate.getContinueRentPriceNumber = SmsActivate.get_continue_rent_price_number
SmsActivate.buyPartnerProduct = SmsActivate.buy_partner_product
