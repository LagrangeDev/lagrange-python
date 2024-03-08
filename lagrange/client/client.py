import asyncio
import os
from typing import Coroutine, Callable, Optional, List

from lagrange.utils.log import logger
from lagrange.utils.operator import timestamp
from lagrange.utils.binary.protobuf import proto_encode, proto_decode
from lagrange.info import DeviceInfo, AppInfo, SigInfo
from lagrange.pb.message.send import SendMsgRsp
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.service.group import (
    PBGroupRecallRequest,
    PBGroupRenameRequest,
    PBRenameMemberRequest,
    PBLeaveGroupRequest,
    PBGetGrpMsgRequest,
    GetGrpMsgRsp
)
from .base import BaseClient
from .event import Events
from .message.elems import T
from .message.encoder import build_message
from .message.decoder import parse_grp_msg
from .wtlogin.sso import SSOPacket
from .server_push import push_handler
from .events.group import GroupMessage
from .highway import HighWaySession


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
        self._highway = HighWaySession(self, logger.fork("highway"))

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
            "OidbSvcTrpcTcp.0x{:0>2X}_{}".format(cmd, sub_cmd),
            proto_encode(body)
        )

    async def push_handler(self, sso: SSOPacket):
        ret = await push_handler.execute(sso.cmd, sso)
        if ret:
            self._events.emit(ret, self)

    async def _send_msg_raw(self, pb: dict, *, uin=0, grp_id=0, uid="") -> SendMsgRsp:
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
        return SendMsgRsp.decode(packet.data)

    async def send_grp_msg(self, msg_chain: List[T], grp_id: int) -> int:
        result = await self._send_msg_raw(
            build_message(msg_chain),
            grp_id=grp_id
        )
        if result.ret_code:
            raise AssertionError(result.ret_code, result.err_msg)
        return result.seq

    async def get_grp_msg(self, grp_id: int, start: int, end: int = 0) -> List[GroupMessage]:
        payload = await self.send_uni_packet(
            "trpc.msg.register_proxy.RegisterProxy.SsoGetGroupMsg",
            PBGetGrpMsgRequest.build(grp_id, start, end or start).encode()
        )
        ret = GetGrpMsgRsp.decode(payload.data).body

        assert ret.grp_id == grp_id and ret.start_seq == start and ret.end_seq == (end or start), "return args not matched"
        return [parse_grp_msg(MsgPushBody.decode(i)) for i in ret.elems]

    async def recall_grp_msg(self, grp_id: int, seq: int):
        payload = await self.send_uni_packet(
            "trpc.msg.msg_svc.MsgService.SsoGroupRecallMsg",
            PBGroupRecallRequest.build(grp_id, seq).encode()
        )
        result = proto_decode(payload.data)
        if result[2] != b"Success":
            raise AssertionError(result)

    async def rename_grp_name(self, grp_id: int, name: str) -> bool:
        try:
            await self.send_oidb_svc(
                0x89A, 15,
                PBGroupRenameRequest.build(grp_id, name).encode()
            )
        except asyncio.TimeoutError:
            return False
        return True

    async def rename_member_name(self, grp_id: int, target_uid: str, name: str) -> bool:  # fixme
        payload = await self.send_oidb_svc(
            0x89A, 15,
            PBRenameMemberRequest.build(grp_id, target_uid, name).encode()
        )
        print(proto_decode(payload.data))

    async def leave_grp(self, grp_id: int) -> bool:
        try:
            await self.send_oidb_svc(
                0x1097, 1,
                PBLeaveGroupRequest.build(grp_id).encode()
            )
        except asyncio.TimeoutError:
            return False
        return True
