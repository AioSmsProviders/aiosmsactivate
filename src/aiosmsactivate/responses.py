from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PurchaseResponse(BaseModel):
    activation_id: int = Field(alias='activationId')
    phone_number: str = Field(alias='phoneNumber')
    activation_cost: float = Field(alias='activationCost')
    country_code: str = Field(alias='countryCode')
    can_get_another_sms: bool = Field(alias='canGetAnotherSms')
    activation_time: str = Field(alias='activationTime')
    activation_operator: str = Field(alias='activationOperator')

    @field_validator('can_get_another_sms')
    def parse_can_get_another_sms(cls, v):
        if v == "1":
            return True
        elif v == "0":
            return False
        else:
            raise ValueError("Input value must be '1' or '0'")


class SetActivationStatusResponse(Enum):
    READY = 'ACCESS_READY'
    RETRY_GET = 'ACCESS_RETRY_GET'
    ACTIVATED = 'ACCESS_ACTIVATION'
    CANCEL = 'ACCESS_CANCEL'
