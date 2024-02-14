import asyncio
from typing import Optional

from lagrange.utils.network import Connection
from lagrange.info import AppInfo, DeviceInfo, SigInfo
from .wtlogin.tlv import CommonTlvBuilder, QrCodeTlvBuilder


class ClientNetwork(Connection):
    default_upstream = ("msfwifi.3g.qq.com", 8080)

    def __init__(self, host: str = "", port: int = 0):
        if not (host and port):
            host, port = self.default_upstream
        super().__init__(host, port)

    def on_connected(self):
        print("connected")

    def on_disconnect(self):
        print("disconnected")

    def on_message(self, msg_len: int):
        print(self.reader.read(msg_len))


class BaseClient:
    """
    A base class for all clients
    login only
    """

    def __init__(
            self,
            uin: int,
            app_info: AppInfo,
            device_info: DeviceInfo,
            sig_info: Optional[SigInfo] = None
    ):
        self._uin = uin
        self._sig = sig_info
        self._app_info = app_info
        self._device_info = device_info
        self._network = ClientNetwork()
        self._loop_task: Optional[asyncio.Task] = None

        self._online = False

    def get_seq(self) -> int:
        try:
            return self._sig.sequence
        finally:
            self._sig.sequence += 1

    def connect(self) -> None:
        if not self._loop_task:
            self._loop_task = asyncio.create_task(self._network.loop())
        else:
            raise RuntimeError("connect call twice")

    async def stop(self):
        await self._network.stop()

    async def wait_closed(self) -> None:
        await self._network.wait_closed()

    @property
    def app_info(self) -> AppInfo:
        return self._app_info

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def seq(self) -> int:
        return self._sig.sequence

    @property
    def uin(self) -> int:
        return self._uin

    @property
    def online(self) -> bool:
        return self._online
