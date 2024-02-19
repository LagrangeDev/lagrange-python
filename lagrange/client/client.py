from typing import Coroutine, Callable, Optional

from lagrange.utils.log import logger
from lagrange.info import DeviceInfo, AppInfo, SigInfo
from .base import BaseClient
from .wtlogin.sso import SSOPacket
from .server_push.binder import push_handler


class Client(BaseClient):
    def __init__(
            self,
            uin: int,
            app_info: AppInfo,
            device_info: DeviceInfo,
            sig_info: Optional[SigInfo] = None,
            sign_provider: Callable[[str, int, bytes], Coroutine[None, None, dict]] = None
    ):
        super().__init__(uin, app_info, device_info, sig_info, sign_provider)

    async def login(self, password="", qrcode_path="./qrcode.png") -> bool:
        try:
            if self._sig.temp_pwd:  # EasyLogin
                await self._key_exchange()

                ret = await self.token_login(self._sig.temp_pwd)
                if ret.successful:
                    return await self.register()
        except:
            logger.login.exception("EasyLogin fail")

        if password:  # PasswordLogin, WIP
            await self._key_exchange()

            while True:
                ret = await self.password_login(password)
                if ret.successful:
                    return await self.register()
                elif ret.captcha_verify:
                    logger.root.warning("captcha verification required")
                    self._sig.captcha_info[0] = input("ticket?->")
                    self._sig.captcha_info[1] = input("rand_str?->")
                else:
                    logger.root.error(f"Unhandled exception raised: {ret.name}")
        else:  # QrcodeLogin
            png, _link = await self.fetch_qrcode()
            logger.root.info(f"save qrcode to '{qrcode_path}'")
            with open(qrcode_path, "wb") as f:
                f.write(png)
            if await self.qrcode_login(3):
                return await self.register()
        return False

    async def push_handler(self, sso: SSOPacket):
        await push_handler.execute(sso.cmd, sso)
