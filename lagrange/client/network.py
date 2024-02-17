"""
ClientNetwork Implement
"""
import asyncio
from typing import Optional, Dict, overload
from typing_extensions import Literal

from lagrange.info import SigInfo
from lagrange.utils.network import Connection

from .sso import parse_sso_header, parse_sso_frame, SSOPacket


class ClientNetwork(Connection):
    default_upstream = ("msfwifi.3g.qq.com", 8080)

    def __init__(self, sig_info: SigInfo, host: str = "", port: int = 0):
        if not (host and port):
            host, port = self.default_upstream
        super().__init__(host, port)

        self._wait_fut_map: Dict[int, asyncio.Future[SSOPacket]] = {}
        self.conn_event = asyncio.Event()
        self._sig = sig_info

    async def write(self, buf: bytes):
        await self.conn_event.wait()
        self.writer.write(buf)
        await self.writer.drain()

    @overload
    async def send(self, buf: bytes, wait_seq: Literal["-1"] = -1, timeout=5) -> None:
        ...

    @overload
    async def send(self, buf: bytes, wait_seq=-1, timeout=5) -> SSOPacket:
        ...

    async def send(self, buf: bytes, wait_seq=-1, timeout=5):
        await self.write(buf)
        if wait_seq != -1:
            fut: asyncio.Future[SSOPacket] = asyncio.Future()
            self._wait_fut_map[wait_seq] = fut
            try:
                await asyncio.wait_for(fut, timeout=timeout)
                return fut.result()
            # except asyncio.TimeoutError as e:
            #     raise e
            finally:
                self._wait_fut_map.pop(wait_seq)  # noqa

    async def on_connected(self):
        self.conn_event.set()
        host, port = self.writer.get_extra_info('peername')
        print(f"connected to {host}:{port}")

    async def on_disconnect(self):
        self.conn_event.clear()
        print("disconnected")

    async def on_message(self, msg_len: int):
        raw = await self.reader.readexactly(msg_len)
        enc_flag, uin, sso_body = parse_sso_header(raw, self._sig.d2_key)
        print(f"uin={uin}, enc={enc_flag} in sso header")

        packet = parse_sso_frame(sso_body, enc_flag == 2)
        if packet.ret_code != 0:
            raise AssertionError(packet.ret_code)

        if packet.seq not in self._wait_fut_map:
            print(f"unknown packet seq: {packet.seq}, ignore")
        else:
            self._wait_fut_map[packet.seq].set_result(packet)
