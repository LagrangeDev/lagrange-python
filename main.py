import os
import asyncio
from lagrange.utils.sign import sign_provider
from lagrange.client.base import BaseClient
from lagrange.info.app import app_list
from lagrange.info.device import DeviceInfo
from lagrange.info.sig import SigInfo

DEVICE_INFO_PATH = "./device_info.json"
SIGINFO_PATH = "./sig_info.bin"


class InfoManager:
    def __init__(self, uin: int, device_info_path: str, sig_info_path: str):
        self.uin: int = uin
        self.device_info_path: str = device_info_path
        self.sig_info_path: str = sig_info_path
        self._device = None
        self._sig_info = None

    @property
    def device(self) -> DeviceInfo:
        assert self._device, "Device not initialized"
        return self._device

    @property
    def sig_info(self) -> SigInfo:
        assert self._sig_info, "SigInfo not initialized"
        return self._sig_info

    def __enter__(self):
        if os.path.isfile(self.device_info_path):
            with open(self.device_info_path, "rb") as f:
                self._device = DeviceInfo.load(f.read())
        else:
            print(f"{self.device_info_path} not found, generating...")
            self._device = DeviceInfo.generate(self.uin)

        if os.path.isfile(self.sig_info_path):
            with open(self.sig_info_path, "rb") as f:
                self._sig_info = SigInfo.load(f.read())
        else:
            print(f"{self.sig_info_path} not found, generating...")
            self._sig_info = SigInfo.new(8848)
        return self

    def __exit__(self, *_):
        # with open(self.sig_info_path, "wb") as f:
        #     f.write(self._sig_info.dump())

        with open(self.device_info_path, "wb") as f:
            f.write(self._device.dump())

        print("device info saved")


async def main():
    qrlogin = False
    uin = 0
    pwd = "<PWD>"
    sign_url = "https://sign.libfekit.so/api/sign"

    app = app_list["linux"]

    with InfoManager(uin, DEVICE_INFO_PATH, SIGINFO_PATH) as im:
        client = BaseClient(
            uin if not qrlogin else 0,
            app,
            im.device,
            im.sig_info,
            sign_provider(sign_url) if sign_url else None
        )
        client.connect()
        #print(f"{round(await client.sso_heartbeat(True) * 1000, 2)}ms")
        if not qrlogin and uin:
            if not im.sig_info.exchange_key:
                await client._key_exchange()
            if im.sig_info.temp_pwd:
                if await client.token_login(im.sig_info.temp_pwd):
                    if await client.register():
                        print("login successful")
            else:
                await client.password_login(pwd)
                it = input("ticket?->")
                ir = input("rand_str?->")
                client._sig.captcha_info[0] = it
                client._sig.captcha_info[1] = ir
                await client.password_login(pwd)
        else:
            png, _link = await client.fetch_qrcode()
            print("save to qrcode.png")
            with open("qrcode.png", "wb") as f:
                f.write(png)
            if await client.qrcode_login(3):
                if await client.register():
                    print("login successful")
            print("done")
        await client.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
