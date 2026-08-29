import json
from typing import Optional

from lagrange.info import AppInfo
from typing_extensions import Literal
import asyncio

from .client.client import Client as Client
# from .client.server_push.msg import msg_push_handler
# from .client.server_push.service import server_kick_handler
from .utils.log import log as log
from .utils.log import install_loguru as install_loguru
from .utils.sign import sign_provider
from .info import InfoManager
from .info.app import app_list
from .utils.binary.protobuf.models import evaluate_all


class Lagrange:
    client: Client

    def __init__(
        self,
        uin: int,
        protocol: Literal["linux", "macos", "windows", "custom"] = "linux",
        sign_url: Optional[str] = None,
        device_info_path="./device.json",
        signinfo_path="./sig.bin",
        custom_protocol_path="./protocol.json",
    ):
        self.scheduled_tasks = []  # 添加这行来存储计划任务
        self.im = InfoManager(uin, device_info_path, signinfo_path)
        self.uin = uin
        self._sign_url = sign_url
        self.sign = None
        self.events = {}
        self.log = log
        self._protocol = protocol
        self._protocol_path = custom_protocol_path

    def subscribe(self, event, handler):
        self.events[event] = handler

    async def login(self, client: Client):
        if self.im.sig_info.d2:
            if not await client.register():
                return await client.login()
            return True
        else:
            return await client.login()
    def schedule_task(self, task):
        """添加计划任务"""
        self.scheduled_tasks.append(task)

    async def run(self):
        if self._protocol == "custom":
            log.root.debug("load custom protocol from %s" % self._protocol_path)
            with open(self._protocol_path, "r") as f:
                proto = json.loads(f.read())
            app_info = AppInfo.load_custom(proto)
        else:
            app_info = app_list[self._protocol]
        log.root.info(f"AppInfo: platform={app_info.os}, ver={app_info.build_version}({app_info.sub_app_id})")

        with self.im as im:
            if self._sign_url:
                self.sign = sign_provider(
                    self._sign_url,
                    self.uin,
                    im.device.guid,
                    app_info.qua,
                )
            self.client = Client(
                self.uin,
                app_info,
                im.device,
                im.sig_info,
                self.sign,
            )
            for event, handler in self.events.items():
                self.client.events.subscribe(event, handler)
            self.client.connect()
            status = await self.login(self.client)
        if not status:
            log.login.error("Login failed")
            return
                    # 登录成功后执行计划任务
        for task in self.scheduled_tasks:
            asyncio.create_task(task(self.client))
        await self.client.wait_closed()

    def launch(self):
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            self.client._task_clear()
            log.root.info("Program exited by user")
        else:
            log.root.info("Program exited normally")


evaluate_all()
