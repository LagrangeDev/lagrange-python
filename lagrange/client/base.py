import asyncio
import hashlib
import time
from typing import Callable, Coroutine, Dict, Optional, Tuple, Union, overload

from typing_extensions import Literal

from lagrange.info import AppInfo, DeviceInfo, SigInfo
from lagrange.utils.binary.reader import Reader
from lagrange.utils.log import log
from lagrange.client.wtlogin.ntlogin import (
    build_ntlogin_request,
    parse_ntlogin_response,
)

from .network import ClientNetwork
from .packet import PacketBuilder
from .wtlogin.enum import LoginErrorCode, QrCodeResult
from .wtlogin.exchange import build_key_exchange_request, parse_key_exchange_response
from .wtlogin.oicq import (
    build_code2d_packet,
    build_login_packet,
    build_uni_packet,
    decode_login_response,
)
from .wtlogin.sso import SSOPacket
from .wtlogin.status_service import (
    build_register_request,
    build_sso_heartbeat_request,
    parse_register_response,
)
from .wtlogin.tlv import CommonTlvBuilder, QrCodeTlvBuilder


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
        sig_info: SigInfo,
        sign_provider: Optional[
            Callable[[str, int, bytes], Coroutine[None, None, dict]]
        ] = None,
        use_ipv6=True,
    ):
        if uin and not sig_info.uin:
            sig_info.uin = uin

        self._uin = uin
        self._sig = sig_info
        self._app_info = app_info
        self._device_info = device_info
        self._heartbeat_interval = 120
        self._captcha_info = ["", "", ""]  # ticket, rand_str, aid

        self._server_push_queue: asyncio.Queue[SSOPacket] = asyncio.Queue()
        self._tasks: Dict[str, asyncio.Task] = {}
        self._network = ClientNetwork(
            sig_info,
            self._server_push_queue,
            self._reconnect_cb,
            self._disconnect_cb,
            use_v6=use_ipv6,
        )
        self._sign_provider = sign_provider

        self._t106 = bytes()
        self._t16a = bytes()

        self._online = asyncio.Event()

    async def _reconnect_cb(self):
        await self.register()

    async def _disconnect_cb(self, recover: bool):
        self._online.clear()
        if not recover:
            await self.stop()

    def destroy_network(self):
        """force run reconnect logic"""
        self._network.destroy_connection()

    def get_seq(self) -> int:
        try:
            return self._sig.sequence
        finally:
            if self._sig.sequence >= 0x8000:
                self._sig.sequence = 0
            self._sig.sequence += 1

    def connect(self) -> None:
        if "loop" not in self._tasks:
            self._tasks["loop"] = asyncio.create_task(self._network.loop())
            self._tasks["push_handle"] = asyncio.create_task(self._push_handle_loop())
            self._tasks["heartbeat"] = asyncio.create_task(self._heartbeat_task())
        else:
            raise RuntimeError("connect call twice")

    async def disconnect(self):
        self._online.clear()
        await self._network.stop()

    async def stop(self):
        await self.disconnect()
        self._task_clear()

    def _task_clear(self):
        for _, task in self._tasks.items():
            if not task.done():
                task.cancel()
                # wakeup loop if it is blocked by select() with long timeout
                task._loop.call_soon_threadsafe(lambda: None)

    async def _heartbeat_task(self):
        err_count = 0
        while True:
            await self.online.wait()
            if not err_count:
                await asyncio.sleep(self._heartbeat_interval)
            try:
                log.network.info(
                    f"{await self.sso_heartbeat(True, 5) * 1000:.2f}ms to server"
                )
            except asyncio.TimeoutError:
                if err_count < 3:
                    log.network.warning("heartbeat timeout")
                    err_count += 1
                    continue
                else:
                    log.network.error("too many heartbeats fail, reconnecting...")
                    self.destroy_network()
            err_count = 0

    async def _push_handle_loop(self):
        while True:
            sso = await self._server_push_queue.get()
            try:
                await self.push_handler(sso)
            except Exception as e:
                log.root.exception("Unhandled exception on push handler", exc_info=e)

    async def wait_closed(self) -> None:
        try:
            await self._network.wait_closed()
        except asyncio.CancelledError:
            await self.stop()

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
        return self._sig.uin

    @property
    def uid(self) -> str:
        return self._sig.uid

    @property
    def online(self) -> asyncio.Event:
        return self._online

    @property
    def using_ipv6(self) -> bool:
        return self._network.using_v6

    @overload
    async def send_uni_packet(
        self, cmd: str, buf: bytes, *, timeout=10
    ) -> SSOPacket: ...

    @overload
    async def send_uni_packet(
        self, cmd: str, buf: bytes, send_only: Literal[False], timeout=10
    ) -> SSOPacket: ...

    @overload
    async def send_uni_packet(
        self, cmd: str, buf: bytes, send_only: Literal[True], timeout=10
    ) -> None: ...

    async def send_uni_packet(self, cmd, buf, send_only: bool = False, timeout=10):
        seq = self.get_seq()
        sign = None
        if self._sign_provider:
            sign = await self._sign_provider(cmd, seq, buf)
        packet = build_uni_packet(
            uin=self.uin,
            seq=seq,
            cmd=cmd,
            sign=sign or {},
            app_info=self.app_info,
            device_info=self.device_info,
            sig_info=self._sig,
            body=buf,
        )
        if send_only:
            return await self._network.send(packet, wait_seq=-1, timeout=timeout)
        return await self._network.send(packet, wait_seq=seq, timeout=timeout)

    async def fetch_qrcode(self) -> Union[int, Tuple[bytes, str]]:
        tlv = QrCodeTlvBuilder()
        body = (
            PacketBuilder()
            .write_u16(0)
            .write_u64(0)
            .write_u8(0)
            .write_tlv(
                tlv.t16(
                    self.app_info.app_id,
                    self.app_info.sub_app_id,
                    bytes.fromhex(self.device_info.guid),
                    self.app_info.pt_version,
                    self.app_info.package_name,
                ),
                tlv.t1b(),
                tlv.t1d(self.app_info.misc_bitmap),
                tlv.t33(bytes.fromhex(self.device_info.guid)),
                tlv.t35(self.app_info.pt_os_version),
                tlv.t66(self.app_info.pt_os_version),
                tlv.td1(self.app_info.os, self.device_info.device_name),
            )
            .write_u8(3)
        ).pack()

        packet = build_code2d_packet(self.uin, 0x31, self._app_info, body)

        response = await self.send_uni_packet("wtlogin.trans_emp", packet)
        decrypted = Reader(response.data)
        decrypted.read_bytes(54)
        ret_code = decrypted.read_u8()
        qrsig = decrypted.read_bytes_with_length("u16", False)
        tlvs = decrypted.read_tlv()

        if not ret_code and tlvs[0x17]:
            self._sig.qrsig = qrsig
            urlreader = Reader(tlvs[209])
            urlreader.read_u8()
            return tlvs[0x17], urlreader.read_bytes_with_length("u8", False).decode()

        return ret_code

    async def get_qrcode_result(self) -> QrCodeResult:
        if not self._sig.qrsig:
            raise AssertionError("No QrSig found, execute fetch_qrcode first")

        body = (
            PacketBuilder()
            .write_bytes(self._sig.qrsig, "u16", False)
            .write_u64(0)
            .write_u32(0)
            .write_u8(0)
            .write_u8(0x03)
        ).pack()

        response = await self.send_uni_packet(
            "wtlogin.trans_emp",
            build_code2d_packet(0, 0x12, self.app_info, body),  # self.uin
        )

        reader = Reader(response.data)
        # length = reader.read_u32()
        reader.read_bytes(8)  # 4 + 4
        reader.read_u16()  # cmd, 0x12
        reader.read_bytes(40)
        _app_id = reader.read_u32()
        ret_code = QrCodeResult(reader.read_u8())

        if ret_code == 0:
            reader.read_bytes(4)
            self._sig.uin = reader.read_u32()
            reader.read_bytes(4)
            t = reader.read_tlv()
            self._t106 = t[0x18]
            self._t16a = t[0x19]
            self._sig.tgtgt = t[0x1E]

        return ret_code

    async def _key_exchange(self):
        packet = await self.send_uni_packet(
            "trpc.login.ecdh.EcdhService.SsoKeyExchange",
            build_key_exchange_request(self.uin, self.device_info.guid),
        )
        parse_key_exchange_response(packet.data, self._sig)

    def submit_login_captcha(self, ticket: str, rand_str: str):
        self._captcha_info[0] = ticket
        self._captcha_info[1] = rand_str

    async def password_login(self, password: str) -> LoginErrorCode:
        md5_passwd = hashlib.md5(password.encode()).digest()

        cr = CommonTlvBuilder().t106(
            self.app_info.app_id,
            self.app_info.app_client_version,
            self.uin,
            md5_passwd,
            self.device_info.guid,
            self._sig.tgtgt,
        )[4:]
        packet = await self.send_uni_packet(
            "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLogin",
            build_ntlogin_request(
                self.uin,
                self.app_info,
                self.device_info,
                self._sig,
                self._captcha_info,
                cr,
            ),
        )

        return parse_ntlogin_response(packet.data, self._sig, self._captcha_info)

    async def token_login(self, token: bytes) -> LoginErrorCode:
        packet = await self.send_uni_packet(
            "trpc.login.ecdh.EcdhService.SsoNTLoginEasyLogin",
            build_ntlogin_request(
                self.uin,
                self.app_info,
                self.device_info,
                self._sig,
                self._captcha_info,
                token,
            ),
        )

        return parse_ntlogin_response(packet.data, self._sig, self._captcha_info)

    async def qrcode_login(self, refresh_interval=5) -> bool:
        if not self._sig.qrsig:
            raise AssertionError("No QrSig found, fetch qrcode first")

        ret_code = QrCodeResult.waiting_for_scan
        while not self._network.closed:
            await asyncio.sleep(refresh_interval)
            ret_last = await self.get_qrcode_result()
            if ret_code != ret_last:
                log.login.info(
                    f"qrcode state changed: {ret_code.name}->{ret_last.name}"
                )
                ret_code = ret_last
            if not ret_code.waitable:
                if not ret_code.success:
                    raise AssertionError(ret_code.name)
                else:
                    break

        tlv = CommonTlvBuilder()
        app = self.app_info
        device = self.device_info
        body = (
            PacketBuilder()
            .write_u16(0x09)
            .write_tlv(
                PacketBuilder().write_bytes(self._t106).pack(0x106),
                tlv.t144(self._sig.tgtgt, app, device),
                tlv.t116(app.sub_sigmap),
                tlv.t142(app.package_name),
                tlv.t145(bytes.fromhex(device.guid)),
                tlv.t18(0, app.app_client_version, self.uin),
                tlv.t141(b"Unknown"),
                tlv.t177(app.wtlogin_sdk),
                tlv.t191(),
                tlv.t100(5, app.app_id, app.sub_app_id, 8001, app.main_sigmap),
                tlv.t107(),
                tlv.t318(),
                PacketBuilder().write_bytes(self._t16a).pack(0x16A),
                tlv.t166(5),
                tlv.t521(),
            )
        ).pack()

        response = await self.send_uni_packet(
            "wtlogin.login", build_login_packet(self.uin, "wtlogin.login", app, body)
        )

        return decode_login_response(response.data, self._sig)

    async def register(self) -> bool:
        response = await self.send_uni_packet(
            "trpc.qq_new_tech.status_svc.StatusService.Register",
            build_register_request(self.app_info, self.device_info),
        )
        if parse_register_response(response.data):
            self._online.set()
            log.login.info("Register successful")
            return True
        log.login.error("Register failure")
        return False

    async def sso_heartbeat(self, calc_latency=False, timeout=10) -> float:
        start_time = time.time()
        await self.send_uni_packet(
            "trpc.qq_new_tech.status_svc.StatusService.SsoHeartBeat",
            build_sso_heartbeat_request(),
            timeout=timeout,
        )
        if calc_latency:
            return time.time() - start_time
        return 0

    async def push_handler(self, sso: SSOPacket):
        pass
