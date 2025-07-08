import datetime
from enum import Enum
import time
from typing import Any

from pydantic import BaseModel, Field, field_validator

from aiosmsactivate.types import SetActivationStatus

not_standart_activate_times = {
    'ya':60*40,
    'ft':60*60,
    'ig':60*60,
    'cy':60*60,
    'wx':60*60,
}

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
    service: str
    activation_unix_time: float | None = None
    time_life: float | None = None
    end_activation_time: float | None = None
    
    _smsactivate_instance: Any = None
    
    def model_post_init(self, __context):
        dt = datetime.datetime.strptime(self.activation_time, "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(dt.timetuple())
        self.activation_unix_time = int(timestamp)
        self.time_life = 60*20 if self.service not in not_standart_activate_times.keys() else not_standart_activate_times[self.service]
        self.end_activation_time = int(timestamp) + self.time_life
    
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
        

class Service(BaseModel):
    code: str
    name: str
    country: str | int
    price: str | float
    retail_price: float
    free_price_map: dict
    count: str | int # physical + virtual numbers
    physical_count: str | int # physical numbers
