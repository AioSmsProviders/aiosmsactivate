from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from aiosmsactivate.types import SetActivationStatus

class Sms(BaseModel):
    date_time: str = Field(alias='dateTime')
    code: str = Field(alias='code')
    text: str = Field(alias='text')
    
class Call(BaseModel):
    from_call: str = Field(alias='from')
    text: str = Field(alias='text')
    code: str = Field(alias='code')
    date_time: str = Field(alias='dateTime')
    url: str | None = Field(alias='url', default=None)
    parcing_count: int = Field(alias='parsingCount')
    
class SetActivationStatusResponse(Enum):
    READY = 'ACCESS_READY'
    RETRY_GET = 'ACCESS_RETRY_GET'
    ACTIVATED = 'ACCESS_ACTIVATION'
    CANCEL = 'ACCESS_CANCEL'
    
class ActivationData(BaseModel):
    verification_type: int | None = Field(alias='verificationType', default=None)
    sms: Sms | None = Field(alias='sms', default=None)
    call: Call | None = Field(alias='call', default=None)
    
    
class Number(BaseModel):
    activation_id: int = Field(alias='activationId')
    phone_number: str = Field(alias='phoneNumber')
    activation_cost: float = Field(alias='activationCost')
    country_code: str = Field(alias='countryCode')
    can_get_another_sms: bool = Field(alias='canGetAnotherSms')
    activation_time: str = Field(alias='activationTime')
    operator: str = Field(alias='activationOperator')
    
    _smsactivate_instance: Any = None
    
    @classmethod
    def from_response(cls, smsactivate_instance, data: dict):
        obj = cls(**data)
        obj._smsactivate_instance = smsactivate_instance
        return obj
    
    async def wait_sms_code(self, timeout: int = 60*5, per_attempt: int = 5) -> Sms | str | int | None:
        self._smsactivate_instance.wait_sms_code(self.activation_id, timeout, per_attempt)
        
    async def set_activation_status(self, status: SetActivationStatus | int,
                                    forward: str | None = None) -> SetActivationStatusResponse:
        self._smsactivate_instance.set_activation_status(self.activation_id, status, forward)
        
    async def get_activation_status(self) -> ActivationData | str:
        self._smsactivate_instance.get_activation_status(self.activation_id)
