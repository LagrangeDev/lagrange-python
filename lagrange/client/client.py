import os
from typing import Coroutine, Callable, Optional, List

from lagrange.utils.log import logger
from lagrange.utils.operator import timestamp
from lagrange.utils.binary.protobuf import proto_encode, proto_decode
from lagrange.info import DeviceInfo, AppInfo, SigInfo
from .base import BaseClient
from .event import Events
from .message.elems import T
from .message.encoder import build_message
from .wtlogin.sso import SSOPacket
from .server_push import push_handler


class Client(BaseClient):
    def __init__(
            self,
            uin: int,
            app_info: AppInfo,
            device_info: DeviceInfo,
            sig_info: Optional[SigInfo] = None,
            sign_provider: Callable[[str, int, bytes], Coroutine[None, None, dict]] = None
    ):
        super().__init__(uin, app_info, device_info, sig_info, sign_provider)

        self._events = Events()

    @property
    def events(self) -> Events:
        return self._events

    async def login(self, password="", qrcode_path="./qrcode.png") -> bool:
        try:
            if self._sig.temp_pwd:  # EasyLogin
                await self._key_exchange()

                ret = await self.token_login(self._sig.temp_pwd)
                if ret.successful:
                    return await self.register()
        except:
            logger.login.exception("EasyLogin fail")

        if password:  # PasswordLogin, WIP
            await self._key_exchange()

            while True:
                ret = await self.password_login(password)
                if ret.successful:
                    return await self.register()
                elif ret.captcha_verify:
                    logger.root.warning("captcha verification required")
                    self._sig.captcha_info[0] = input("ticket?->")
                    self._sig.captcha_info[1] = input("rand_str?->")
                else:
                    logger.root.error(f"Unhandled exception raised: {ret.name}")
        else:  # QrcodeLogin
            png, _link = await self.fetch_qrcode()
            logger.root.info(f"save qrcode to '{qrcode_path}'")
            with open(qrcode_path, "wb") as f:
                f.write(png)
            if await self.qrcode_login(3):
                return await self.register()
        return False

    async def send_oidb_svc(self, cmd: int, sub_cmd: int, buf: bytes, is_uid=False) -> SSOPacket:
        body = {
            1: cmd,
            2: sub_cmd,
            4: buf,
            12: is_uid
        }
        return await self.send_uni_packet(
            "OidbSvcTrpcTcp.0x{:0>2x}_{}".format(cmd, sub_cmd),
            proto_encode(body)
        )

    async def push_handler(self, sso: SSOPacket):
        ret = await push_handler.execute(sso.cmd, sso)
        if ret:
            self._events.emit(ret, self)

    async def _send_msg_raw(self, pb: dict, *, uin=0, grp_id=0, uid="") -> dict:
        assert uin or grp_id, "uin and grp_id"
        seq = self.seq + 1
        sendto = {}
        if not grp_id:  # friend
            assert uin and uid, "uin and uid must be filled"
            sendto[1] = {1: uin, 2: uid}
        elif grp_id:  # grp
            sendto[2] = {1: grp_id}
        elif uin and grp_id:  # temp msg
            sendto[3] = {1: grp_id, 2: uin}
        else:
            assert False
        body = {
            1: sendto,
            2: {
                1: 1,
                2: 0,
                3: 0
            },
            3: pb,
            4: seq,
            5: int.from_bytes(os.urandom(4), byteorder="big", signed=False)
        }
        if not grp_id:
            body[12] = {1: timestamp()}

        packet = await self.send_uni_packet(
            "MessageSvc.PbSendMsg",
            proto_encode(body)
        )
        return proto_decode(packet.data)

    async def send_grp_msg(self, msg_chain: List[T], grp_id: int) -> None:
        await self._send_msg_raw(
            build_message(msg_chain),
            grp_id=grp_id
        )