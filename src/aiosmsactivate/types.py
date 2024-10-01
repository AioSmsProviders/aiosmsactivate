from enum import Enum


class ActivationStatus(int, Enum):
    WAIT = 1
    RETRY = 2
    RESEND = 3
    CANCEL = 4
    OK = 5


class SetActivationStatus(int, Enum):
    READY = 1
    AGAIN = 3
    COMPLETE = 6
    CANCEL = 8
