"""
ClientNetwork Implement
"""
import asyncio
from typing import Callable, Coroutine, Dict, overload

from typing_extensions import Literal

from lagrange.info import SigInfo
from lagrange.utils.log import logger
from lagrange.utils.network import Connection

from .wtlogin.sso import SSOPacket, parse_sso_frame, parse_sso_header


class ClientNetwork(Connection):
    default_upstream = ("msfwifi.3g.qq.com", 8080)

    def __init__(
        self,
        sig_info: SigInfo,
        push_store: asyncio.Queue[SSOPacket],
        reconnect_cb: Callable[[], Coroutine],
        disconnect_cb: Callable[[], Coroutine],
        host: str = "",
        port: int = 0,
    ):
        if not (host and port):
            host, port = self.default_upstream
        super().__init__(host, port)

        self.conn_event = asyncio.Event()
        self._push_store = push_store
        self._reconnect_cb = reconnect_cb
        self._disconnect_cb = disconnect_cb
        self._wait_fut_map: Dict[int, asyncio.Future[SSOPacket]] = {}
        self._connected = False
        self._sig = sig_info

    async def write(self, buf: bytes):
        await self.conn_event.wait()
        self.writer.write(buf)
        await self.writer.drain()

    @overload
    async def send(self, buf: bytes, wait_seq: Literal["-1"] = -1, timeout=10) -> None:
        ...

    @overload
    async def send(self, buf: bytes, wait_seq=-1, timeout=10) -> SSOPacket:
        ...

    async def send(self, buf: bytes, wait_seq=-1, timeout=10):
        await self.write(buf)
        if wait_seq != -1:
            fut: asyncio.Future[SSOPacket] = asyncio.Future()
            self._wait_fut_map[wait_seq] = fut
            try:
                await asyncio.wait_for(fut, timeout=timeout)
                return fut.result()
            finally:
                self._wait_fut_map.pop(wait_seq)  # noqa

    async def on_connected(self):
        self.conn_event.set()
        host, port = self.writer.get_extra_info("peername")
        logger.network.info(f"Connected to {host}:{port}")
        if self._connected and not self._stop_flag:
            t = asyncio.create_task(self._reconnect_cb(), name="reconnect_cb")
        else:
            self._connected = True

    async def on_disconnect(self):
        self.conn_event.clear()
        logger.network.warning("Connection lost")
        t = asyncio.create_task(self._disconnect_cb(), name="disconnect_cb")

    async def on_error(self) -> bool:
        logger.network.exception("Connection got an unexpected error:")
        return True

    async def on_message(self, msg_len: int):
        raw = await self.reader.readexactly(msg_len)
        enc_flag, uin, sso_body = parse_sso_header(raw, self._sig.d2_key)

        packet = parse_sso_frame(sso_body, enc_flag == 2)

        if packet.seq > 0:  # uni rsp
            logger.network.debug(
                f"{packet.seq}({packet.ret_code})-> {packet.cmd or packet.extra}"
            )
            if packet.ret_code != 0 and packet.seq in self._wait_fut_map:
                return self._wait_fut_map[packet.seq].set_exception(
                    AssertionError(packet.ret_code, packet.extra)
                )
            elif packet.ret_code != 0:
                return logger.network.error(
                    f"Unexpected error on sso layer: {packet.ret_code}: {packet.extra}"
                )

            if packet.seq not in self._wait_fut_map:
                logger.network.warning(
                    f"Unknown packet: {packet.cmd}({packet.seq}), ignore"
                )
            else:
                self._wait_fut_map[packet.seq].set_result(packet)
        else:  # server pushed
            logger.network.debug(
                f"{packet.seq}({packet.ret_code})<- {packet.cmd or packet.extra}"
            )
            await self._push_store.put(packet)
