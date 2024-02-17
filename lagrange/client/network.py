"""
ClientNetwork Implement
"""
import asyncio
import struct
from io import BytesIO
from typing import Optional, Dict

from lagrange.info import SigInfo
from lagrange.utils.crypto.ecdh import ecdh
from lagrange.utils.crypto.tea import qqtea_decrypt
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

    async def send(self, buf: bytes, wait_seq=-1, timeout=5) -> Optional[SSOPacket]:
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
        _enc_flag, uin, sso_body = parse_sso_header(raw, self._sig.d2_key)
        print(f"uin={uin} in sso header")

        packet = parse_sso_frame(sso_body)
        if packet.ret_code != 0:
            raise AssertionError(packet.ret_code)

        data = packet.data
        print(data.hex())
        data = qqtea_decrypt(data[16:], ecdh["secp192k1"].share_key)

        dio = BytesIO(data)
        print(dio.read(54))
        ret_code, qrsig = struct.unpack(">BH", dio.read(3))
        dio.read(2)
        print(ret_code, qrsig)
        print(dio.read())