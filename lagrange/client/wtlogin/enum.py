from enum import IntEnum


class QrCodeResult(IntEnum):
    confirmed = 0
    expired = 17
    waiting_for_scan = 48
    waiting_for_confirm = 53
    canceled = 54

    @property
    def waitable(self) -> bool:
        if self in (self.waiting_for_scan, self.waiting_for_confirm):
            return True
        return False

    @property
    def success(self) -> bool:
        return self == self.confirmed
