import json
import re

import aiohttp

from .exceptions import SmsActivateException
from .responses import PurchaseResponse, SetActivationStatusResponse
from .types import SetActivationStatus, ActivationStatus


class SmsActivate:

    def __init__(self, api_key: str):
        self._api_key = api_key

    async def __send_request(self, action: str, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.request('POST', 'https://api.sms-activate.io/stubs/handler_api.php', **kwargs, params={
                'api_key': self._api_key,
                'action': action,
                **(kwargs['params'] if 'params' in kwargs else {})
            }) as response:
                return await response.text()

    async def get_balance(self) -> float:
        pattern = re.compile(r'ACCESS_BALANCE:(\d+\.\d{2})')
        response = await self.__send_request('getBalance')
        match = pattern.match(response)
        if not match:
            raise SmsActivateException('Invalid response sequence')

        return float(match.group(1))

    async def get_available_countries(self, service: str) -> dict[str, ...]:
        response = await self.__send_request('getTopCountriesByService', params={
            'service': service
        })
        return json.loads(response)

    async def get_activation_status(self, activation_id: str) -> tuple[ActivationStatus, str | None]:
        response = await self.__send_request('getStatus', params={
            'id': activation_id
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

    async def purchase(self, service: str, forward: bool | None = None, max_price: float | None = None,
                       phone_exception: str | None = None, operator: str | None = None,
                       verification: bool | None = None,
                       ref: str | None = None, country: str | None = None,
                       use_cashback: bool | None = None) -> PurchaseResponse:
        response = await self.__send_request('getNumberV2', params={
            'service': service,
            **({'forward': 1 if forward else 0} if forward is not None else {}),
            **({'maxPrice': str(max_price)} if max_price is not None else {}),
            **({'phoneException': phone_exception} if phone_exception is not None else {}),
            **({'operator': operator} if operator is not None else {}),
            **({'verification': str(verification)} if verification is not None else {}),
            **({'ref': ref} if ref is not None else {}),
            **({'country ': country} if country is not None else {}),
            **({'useCashBack': str(use_cashback)} if use_cashback is not None else {}),
        })

        return PurchaseResponse(**json.loads(response))

    async def set_activation_status(self, activation_id: str, status: SetActivationStatus,
                                    forward: str | None = None) -> SetActivationStatusResponse:
        members = {member.value: member for member in SetActivationStatusResponse}

        response = await self.__send_request('setStatus', params={
            'id': activation_id,
            'status': status.value,
            **({'forward': forward} if forward is not None else {})
        })

        return members[response]
