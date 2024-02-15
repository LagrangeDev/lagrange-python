import asyncio
from typing import Optional

from lagrange.utils.binary.builder import Builder
from lagrange.utils.network import Connection
from lagrange.info import AppInfo, DeviceInfo, SigInfo
from .wtlogin.tlv import CommonTlvBuilder, QrCodeTlvBuilder
from .oicq import build_code2d_packet


class ClientNetwork(Connection):
    default_upstream = ("msfwifi.3g.qq.com", 8080)

    def __init__(self, host: str = "", port: int = 0):
        if not (host and port):
            host, port = self.default_upstream
        super().__init__(host, port)
        self.conn_event = asyncio.Event()

    async def write(self, buf: bytes):
        await self.conn_event.wait()
        self.writer.write(buf)
        await self.writer.drain()

    async def on_connected(self):
        self.conn_event.set()
        print("connected")

    async def on_disconnect(self):
        self.conn_event.clear()
        print("disconnected")

    async def on_message(self, msg_len: int):
        print(await self.reader.read(msg_len), 11)


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

    async def fetch_qrcode(self):
        tlv = QrCodeTlvBuilder()
        body = (
            Builder()
            .write_u16(0)
            .write_u64(0)
            .write_u8(0)
            .write_tlv(
                tlv.t16(
                    self.app_info.app_id,
                    self.app_info.app_id_qrcode,
                    self.device_info.guid.encode(),
                    self.app_info.pt_version,
                    self.app_info.package_name
                ),
                tlv.t1b(),
                tlv.t1d(self.app_info.misc_bitmap),
                tlv.t33(self.device_info.guid.encode()),
                tlv.t35(self.app_info.pt_os_version),
                tlv.t66(self.app_info.pt_os_version),
                tlv.td1(self.app_info.os, self.device_info.device_name)
            ).write_u8(3)
        ).pack()

        packet = build_code2d_packet(
            self.uin,
            self.get_seq(),
            0x31,
            self.app_info,
            self.device_info,
            self._sig,
            body
        )

        await self._network.write(packet)

        print("done")
