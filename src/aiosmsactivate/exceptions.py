import json
from .utils import is_json


api_errors = {
    "BAD_KEY": "Invalid api key",
    "BAD_ACTION": "Incorrect action",
    "BAD_SERVICE": "Incorrect service name",
    "BAD_STATUS": "Incorrect status code, can be set 1,3,6,8",
    "WRONG_ACTIVATION_ID": "invalid parent activation ID",
    "WRONG_DATE": "the date format is not a timestamp or one of the dates later than 30 days",
    "WRONG_MAX_PRICE": "the specified maximum price is less/more than the allowed one",
    "WRONG_EXCEPTION_PHONE": "Incorrect exception prefixes",
    "WRONG_ADDITIONAL_SERVICE": "Invalid additional service (only forwarding services are allowed)",
    "WRONG_SECURITY": "Error when trying to transmit the activation ID without forwarding, or completed/inactive activation",
    "NO_BALANCE": "Not enough money",
    "NO_BALANCE_FORWARD": "not enough money to buy redirects",
    "NO_NUMBERS": "No numbers",
    "NO_ACTIVATION": "Activation ID does not exist",
    "NO_CALL": "The call didn't come",
    "NO_ID_RENT": "The rent ID is not specified",
    "ERROR_SQL": "Error on sql server",
    "ACCOUNT_INACTIVE": "Account is inactive",
    "SERVER_ERROR": "server error",
    "BANNED": "Your account has been temporarily blocked",
    "CHANNELS_LIMIT": "Account blocked",
    "EARLY_CANCEL_DENIED": "You can't cancel a number in the first 2 minutes",
    "OPERATORS_NOT_FOUND": "No records were found (for example, a non-existent country was transmitted)",
    "ORDER_ALREADY_EXISTS": "Order already exist",
    "REPEAT_ADDITIONAL_SERVICE": "Are you trying to order the purchased service again",
    "RENEW_ACTIVATION_NOT_AVAILABLE": "the number is unavailable for additional activation",
    "SIM_OFFLINE": "sim card is offline",
    "NEW_ACTIVATION_IMPOSSIBLE": "It is not possible to make an additional activation",
    "PARSE_COUNT_EXCEED": "Limit of parsing attempts (maximum 4)",
    "INCORECT_STATUS": "The status is missing or incorrectly specified. Can be set 1, 2 for rent",
    "CANT_CANCEL": "It is not possible to cancel the rent (more than 20 minutes)",
    "ALREADY_FINISH": "Rent already finish",
    "ALREADY_CANCEL": "Rent already cancel",
    "INVALID_PHONE": "Incorrect rent id",
    "INVALID_TIME": "Wrong time. The available number of hours is from 4 to 1344",
    "MAX_HOURS_EXCEED": "The maximum available time has been exceeded",
    "RENT_DIE": "The lease cannot be extended because the room's life has expired.",
    "NO_YULA_MAIL": "The purchase of Mail Group activation services is available only to wholesale customers (starting from 1000 numbers per month) who have submitted an application and have been verified by the security service.",
    "NO_ACTIVATIONS": "No records found (no active activations)",
    "INVALID_ACTIVATION_ID": "invalid activation id",
    "OUT_OF_STOCK": "Out of numbers for this country",
    # "STATUS_FINISH": "Rent is paid and completed",
    # "STATUS_CANCEL": "Rent cancelled with a refund",
    # "STATUS_WAIT_CODE": "Wait sms code",
    "STATUS_REVOKE": "The number has been blocked, and your funds have been refunded.",
    "BAD_DATA": "Incorrect id or id is not integer",
    "INVALID_STATUS": "Incorrect status",
    "INVALID_SIGNATURE": "Incorrect key",
}


class SmsActivateException(Exception):
    def __init__(self, code, message: str):
        self.code = code
        self.message = message


def raise_smsactivate_error(response_text: str):
    error_response_text = response_text
    if is_json(response_text):
        resp_data = json.loads(response_text)
        if resp_data.get('status') == 'error':
            error_response_text = resp_data.get('message')
    
    error_code = error_response_text.split(":")[0]
    error_message = error_response_text
    
    if error_code in api_errors.keys():
        raise SmsActivateException(error_code, f'{error_message} - {api_errors[error_code]}')
    