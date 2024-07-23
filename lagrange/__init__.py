from typing import Literal, Optional
import asyncio

from .client.client import Client as Client
from .utils.log import logger
from .utils.sign import sign_provider
from .info import InfoManager
from .info.app import app_list


class Lagrange:
    client: Client

    def __init__(
        self,
        uin: int,
        protocol: Literal["linux", "macos", "windows"] = "linux",
        sign_url: Optional[str] = None,
        device_info_path="./device.json",
        signinfo_path="./sig.bin"
    ):
        self.im = InfoManager(uin, device_info_path, signinfo_path)
        self.uin = uin
        self.info = app_list[protocol]
        self.sign = sign_provider(sign_url) if sign_url else None
        self.events = {}

    def subscribe(self, event, handler):
        self.events[event] = handler

    async def login(self, client: Client):
        if self.im.sig_info.d2:
            if not await client.register():
                return await client.login()
            return True
        else:
            return await client.login()

    async def run(self):
        with self.im as im:
            self.client = Client(
                self.uin,
                self.info,
                im.device,
                im.sig_info,
                self.sign,
            )
            for event, handler in self.events.items():
                self.client.events.subscribe(event, handler)
            self.client.connect()
            status = await self.login(self.client)
        if not status:
            logger.login.error("Login failed")
            return
        await self.client.wait_closed()

    def launch(self):
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            logger.root.info("Program exit")
            self.client._task_clear()
