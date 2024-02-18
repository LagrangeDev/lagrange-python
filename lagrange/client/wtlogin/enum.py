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


class LoginErrorCode(IntEnum):
    token_expired = 140022015
    unusual_verify = 140022011
    login_failure = 140022013
    wrong_captcha = 140022007
    new_device_verify = 140022010
    captcha_verify = 140022008
    success = 0
