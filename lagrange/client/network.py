"""
ClientNetwork Implement
"""

import asyncio
import ipaddress
import sys
from typing import Dict, Callable, Coroutine, Tuple, overload, Optional
from typing_extensions import Literal

from lagrange.info import SigInfo
from lagrange.utils.log import log
from lagrange.utils.network import Connection

from .wtlogin.sso import SSOPacket, parse_sso_frame, parse_sso_header


class ClientNetwork(Connection):
    V4UPSTREAM = ("msfwifi.3g.qq.com", 8080)
    V6UPSTREAM = ("msfwifiv6.3g.qq.com", 8080)

    def __init__(
        self,
        sig_info: SigInfo,
        push_store: asyncio.Queue[SSOPacket],
        reconnect_cb: Callable[[], Coroutine],
        disconnect_cb: Callable[[bool], Coroutine],
        use_v6=False,
        *,
        manual_address: Optional[Tuple[str, int]] = None,
    ):
        if not manual_address:
            host, port = self.V6UPSTREAM if use_v6 else self.V4UPSTREAM
        else:
            host, port = manual_address
        super().__init__(host, port)

        self.conn_event = asyncio.Event()
        self._using_v6 = use_v6
        self._push_store = push_store
        self._reconnect_cb = reconnect_cb
        self._disconnect_cb = disconnect_cb
        self._wait_fut_map: Dict[int, asyncio.Future[SSOPacket]] = {}
        self._connected = False
        self._sig = sig_info

    @property
    def using_v6(self) -> bool:
        if not self.closed:
            return self._using_v6
        raise RuntimeError("Network not connect, execute 'connect' first")

    def destroy_connection(self):
        if self._writer:
            self._writer.close()

    async def write(self, buf: bytes):
        await self.conn_event.wait()
        self.writer.write(buf)
        await self.writer.drain()

    @overload
    async def send(
        self, buf: bytes, wait_seq: Literal[-1], timeout=10
    ) -> None: ...

    @overload
    async def send(self, buf: bytes, wait_seq: int, timeout=10) -> SSOPacket: ...  # type: ignore

    async def send(self, buf: bytes, wait_seq: int, timeout: int = 10):  # type: ignore
        await self.write(buf)
        if wait_seq != -1:
            fut: asyncio.Future[SSOPacket] = asyncio.Future()
            self._wait_fut_map[wait_seq] = fut
            try:
                await asyncio.wait_for(fut, timeout=timeout)
                return fut.result()
            finally:
                self._wait_fut_map.pop(wait_seq)  # noqa

    def _cancel_all_task(self):
        for _, fut in self._wait_fut_map.items():
            if not fut.done():
                fut.cancel("connection closed")

    async def on_connected(self):
        self.conn_event.set()
        host, port = self.writer.get_extra_info("peername")[:2]  # for v6 ip
        if ipaddress.ip_address(host).version != 6 and self._using_v6:
            log.network.debug("using v4 address, disable v6 support")
            self._using_v6 = False
        log.network.info(f"Connected to {host}:{port}")
        if self._connected and not self._stop_flag:
            t = asyncio.create_task(self._reconnect_cb(), name="reconnect_cb")
        else:
            self._connected = True

    async def on_close(self):
        self.conn_event.clear()
        log.network.warning("Connection closed")
        self._cancel_all_task()
        t = asyncio.create_task(self._disconnect_cb(False), name="disconnect_cb")

    async def on_error(self) -> bool:
        _, err, _ = sys.exc_info()

        # OSError: timeout
        if isinstance(err, (asyncio.IncompleteReadError, ConnectionError, OSError)):
            log.network.warning("Connection lost, reconnecting...")
            log.network.debug(f"{repr(err)}")
            recover = True
        else:
            log.network.error(f"Connection got an unexpected error: {repr(err)}")
            recover = False
        self._cancel_all_task()
        t = asyncio.create_task(self._disconnect_cb(recover), name="disconnect_cb")
        return recover

    async def on_message(self, message_length: int):
        raw = await self.reader.readexactly(message_length)
        enc_flag, uin, sso_body = parse_sso_header(raw, self._sig.d2_key)

        packet = parse_sso_frame(sso_body, enc_flag == 2)

        if packet.seq > 0:  # uni rsp
            log.network.debug(
                f"{packet.seq}({packet.ret_code})-> {packet.cmd or packet.extra}"
            )
            if packet.ret_code != 0 and packet.seq in self._wait_fut_map:
                return self._wait_fut_map[packet.seq].set_exception(
                    AssertionError(packet.ret_code, packet.extra)
                )
            elif packet.ret_code != 0:
                return log.network.error(
                    f"Unexpected error on sso layer: {packet.ret_code}: {packet.extra}"
                )

            if packet.seq not in self._wait_fut_map:
                log.network.warning(
                    f"Unknown packet: {packet.cmd}({packet.seq}), ignore"
                )
            else:
                self._wait_fut_map[packet.seq].set_result(packet)
        elif packet.seq == 0:
            raise AssertionError(packet.ret_code, packet.extra)
        else:  # server pushed
            log.network.debug(
                f"{packet.seq}({packet.ret_code})<- {packet.cmd or packet.extra}"
            )
            await self._push_store.put(packet)
