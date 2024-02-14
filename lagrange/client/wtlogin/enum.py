from enum import IntEnum


class QrCodeResult(IntEnum):
    confirmed = 0
    expired = 17
    waiting_for_scan = 48
    waiting_for_confirm = 53
    canceled = 54
