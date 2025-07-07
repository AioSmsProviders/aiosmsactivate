import json
import logging
import re
from typing import Literal

import aiohttp

from .utils import is_json
from .exceptions import SmsActivateException
from .responses import SetActivationStatusResponse
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
    на git: https://github.com/AioSmsProviders/aiosmsactivate
    Так же можете писать в чат https://t.me/+5YQ8k6H02bkxZmRi
    или обратиться к главному разработчику с идеями, предложениями и багами: https://t.me/lolkof  
    
    EN  
    Thank you for using my library, you can participate in the development of the library
    on git: https://github.com/AioSmsProviders/aiosmsactivate
    You can also write to the chat https://t.me/+5YQ8k6H02bkxZmRi
    or contact the main developer with ideas, suggestions, and bugs: https://t.me/lolkof
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
                params = kwargs.get('params')
                if params:
                    kwargs.pop('params')
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
                        logging.debug(response.real_url)
                        return await response.text()
            except Exception as e:
                last_exception = e
                continue
            self._accept_url = url
            break

        raise last_exception

    async def get_balance(self, cashback: bool = False) -> float:
        pattern = re.compile(r'ACCESS_BALANCE:(\d+\.\d{2})')
        response = await self.__send_request('getBalance' if not cashback else 'getBalanceAndCashBack')
        match = pattern.match(response)
        if not match:
            raise SmsActivateException('Invalid response sequence')

        return float(match.group(1))
    getBalance = get_balance
    async def get_balance_and_cashback(self):
        return await self.get_balance(cashback=True)
    getBalanceAndCashBack = get_balance_and_cashback

    async def get_available_countries(self, service: str, freePrice: bool | str) -> dict[str, ...]:
        response = await self.__send_request('getTopCountriesByService', params={
            'service': service,
            'freePrice': str(freePrice).lower()
        })
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    getTopCountriesByService = get_available_countries
    
    async def get_count_numbers(self, country: str, operator: str) -> dict[str, ...]:
        response = await self.__send_request('getNumbersStatus', params={
            'country': country,
            'operator': operator
        })
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    getNumbersStatus = get_count_numbers
    
    async def get_operators(self, country: str = None) -> dict[str, ...]:
        params = {}
        if country is not None:
            params["country"] = country
        response = await self.__send_request('getOperators', params=params)
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    getOperators = get_operators
    
    async def get_active_activations(self) -> dict[str, ...]:
        response = await self.__send_request('getActiveActivations')
        
        if not is_json(response):
            return response
        
        return json.loads(response)
    getActiveActivations = get_active_activations

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
    getStatus = get_activation_status_v1
    
    async def get_activation_status(self, id: str) -> tuple[ActivationStatus, str | None] | dict:
        response = await self.__send_request('getStatusV2', params={
            'id': id
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getStatusV2 = get_activation_status

    async def purchase(self, service: str, forward: bool | None = None, maxPrice: float | None = None,
                       phoneException: str | None = None, operator: str | None = None,
                       activationType: int | str | None = None, language: str | None = None,
                       userId: str | int | None = None,
                       ref: str | None = None, country: str | None = None,
                       useCashBack: bool | None = None,
                       orderId: str | int | None = None,
                       _is_v2: bool = True
                       ) -> dict | str:
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
        
        return json.loads(response)
    getNumberV2 = purchase
    
    async def getNumber(self, *args, **kwargs):
        kwargs["_is_v2"] = False
        return await self.purchase(*args, **kwargs)
    purchase_v1 = getNumber
    
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
    getMultiServiceNumber = get_multi_service_number
    

    async def set_activation_status(self, id: str, status: SetActivationStatus,
                                    forward: str | None = None) -> SetActivationStatusResponse:
        members = {member.value: member for member in SetActivationStatusResponse}

        response = await self.__send_request('setStatus', params={
            'id': id,
            'status': status.value,
            **({'forward': forward} if forward is not None else {})
        })

        return members[response]
    setStatus = set_activation_status

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
    getHistory = get_history
    
    async def get_list_top_countries(self, 
                          service: str,
                       ) -> dict | list:
        response = await self.__send_request('getListOfTopCountriesByService', params={
            'service': service
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getListOfTopCountriesByService = get_list_top_countries
    
    async def get_incoming_call_status(self, 
                          id: str | int = None,
                       ) -> dict | list:
        response = await self.__send_request('getIncomingCallStatus', params={
            'activationId': id
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getIncomingCallStatus = get_incoming_call_status
    
    async def get_prices(self, 
                          service: str = None,
                          country: str = None,
                       ) -> dict | list:
        response = await self.__send_request('getPrices', params={
            **({'service': str(service)} if service is not None else {}),
            **({'country': str(country)} if country is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getPrices = get_prices
    
    async def get_prices_verification(self, 
                          service: str = None,
                       ) -> dict | list:
        response = await self.__send_request('getPricesVerification', params={
            **({'service': str(service)} if service is not None else {}),
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getPricesVerification = get_prices_verification
    
    async def get_countries(self,
                       ) -> dict | list:
        response = await self.__send_request('getCountries', params={
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getCountries = get_countries
    
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
    getServicesList = get_service_list
    
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
    getAdditionalService = get_additional_service
    
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
    getExtraActivation = get_extra_activation
    
    async def check_extra_activation(self, 
                          activationId: str | int
                       ) -> dict | list:
        response = await self.__send_request('checkExtraActivation', params={
            'activationId': str(activationId)
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    checkExtraActivation = check_extra_activation
    
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
    parseCall = parse_call
    
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
    getRentServicesAndCountries = get_rent_services_and_countries
    
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
    getRentNumber = get_rent_number
    
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
    getRentStatus = get_rent_status
    
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
    getRentStatus = get_rent_status
    
    async def get_rent_list(self,
                       ) -> dict | str:
        response = await self.__send_request('getRentList', params={
        })

        if not is_json(response):
            return response
        
        return json.loads(response)
    getRentList = get_rent_list
    
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
    continueRentNumber = continue_rent_number
    
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
    getContinueRentPriceNumber = get_continue_rent_price_number
    
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
    buyPartnerProduct = buy_partner_product
    