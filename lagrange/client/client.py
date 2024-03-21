import os
from typing import BinaryIO, Callable, Coroutine, List, Optional

from lagrange.info import AppInfo, DeviceInfo, SigInfo
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.message.send import SendMsgRsp
from lagrange.pb.service.comm import SendNudge
from lagrange.pb.service.group import (
    FetchGroupResponse,
    GetGrpMsgRsp,
    PBFetchGroupRequest,
    PBGetGrpMsgRequest,
    PBGroupMuteRequest,
    PBGroupRecallRequest,
    PBGroupRenameRequest,
    PBHandleGroupRequest,
    PBLeaveGroupRequest,
    PBRenameMemberRequest,
    PBSetEssence,
    SetEssenceRsp,
)
from lagrange.pb.service.oidb import OidbRequest, OidbResponse
from lagrange.utils.binary.protobuf import proto_decode, proto_encode
from lagrange.utils.log import logger
from lagrange.utils.operator import timestamp

from .base import BaseClient
from .event import Events
from .events.group import GroupMessage
from .events.service import ClientOnline, ClientOffline
from .highway import HighWaySession
from .message.decoder import parse_grp_msg
from .message.elems import Audio, Image
from .message.encoder import build_message
from .message.types import T
from .server_push import push_handler
from .wtlogin.sso import SSOPacket


class Client(BaseClient):
    def __init__(
        self,
        uin: int,
        app_info: AppInfo,
        device_info: DeviceInfo,
        sig_info: Optional[SigInfo] = None,
        sign_provider: Callable[[str, int, bytes], Coroutine[None, None, dict]] = None,
        use_ipv6=True,
    ):
        super().__init__(uin, app_info, device_info, sig_info, sign_provider, use_ipv6)

        self._events = Events()
        self._highway = HighWaySession(self, logger.fork("highway"))

    @property
    def events(self) -> Events:
        return self._events

    async def register(self) -> bool:
        if await super().register():
            self._events.emit(ClientOnline(), self)
            return True
        self._events.emit(ClientOffline(recoverable=False), self)
        return False

    async def _disconnect_cb(self, from_err: bool):
        await super()._disconnect_cb(from_err)
        self._events.emit(ClientOffline(recoverable=from_err), self)

    async def login(self, password="", qrcode_path="./qrcode.png") -> bool:
        try:
            if self._sig.temp_pwd:  # EasyLogin
                await self._key_exchange()

                rsp = await self.token_login(self._sig.temp_pwd)
                if rsp.successful:
                    return await self.register()
        except Exception as e:
            logger.login.error("EasyLogin fail", exc_info=e)

        if password:  # TODO: PasswordLogin, WIP
            await self._key_exchange()

            while True:
                rsp = await self.password_login(password)
                if rsp.successful:
                    return await self.register()
                elif rsp.captcha_verify:
                    logger.root.warning("captcha verification required")
                    self.submit_login_captcha(
                        ticket=input("ticket?->"), rand_str=input("rand_str?->")
                    )
                else:
                    logger.root.error(f"Unhandled exception raised: {rsp.name}")
        else:  # QrcodeLogin
            png, _link = await self.fetch_qrcode()
            logger.root.info(f"save qrcode to '{qrcode_path}'")
            with open(qrcode_path, "wb") as f:
                f.write(png)
            if await self.qrcode_login(3):
                return await self.register()
        return False

    async def send_oidb_svc(
        self, cmd: int, sub_cmd: int, buf: bytes, is_uid=False
    ) -> OidbResponse:
        rsp = OidbResponse.decode(
            (
                await self.send_uni_packet(
                    "OidbSvcTrpcTcp.0x{:0>2X}_{}".format(cmd, sub_cmd),
                    OidbRequest(
                        cmd=cmd, sub_cmd=sub_cmd, data=bytes(buf), is_uid=is_uid
                    ).encode(),
                )
            ).data
        )
        if rsp.ret_code:
            logger.network.error(
                f"OidbSvc(0x{cmd:X}_{sub_cmd}) return an error: ({rsp.ret_code}){rsp.err_msg}"
            )
        return rsp

    async def push_handler(self, sso: SSOPacket):
        rsp = await push_handler.execute(sso.cmd, sso)
        if rsp:
            self._events.emit(rsp, self)

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
            2: {1: 1, 2: 0, 3: 0},
            3: pb,
            4: seq,
            5: int.from_bytes(os.urandom(4), byteorder="big", signed=False),
        }
        if not grp_id:
            body[12] = {1: timestamp()}

        packet = await self.send_uni_packet("MessageSvc.PbSendMsg", proto_encode(body))
        return SendMsgRsp.decode(packet.data)

    async def send_grp_msg(self, msg_chain: List[T], grp_id: int) -> int:
        result = await self._send_msg_raw(
            {1: build_message(msg_chain).encode()}, grp_id=grp_id
        )
        if result.ret_code:
            raise AssertionError(result.ret_code, result.err_msg)
        return result.seq

    async def upload_grp_image(
        self, image: BinaryIO, grp_id: int, is_emoji=False
    ) -> Image:
        img = await self._highway.upload_image(image, gid=grp_id)
        if is_emoji:
            img.is_emoji = True
        return img

    async def upload_grp_audio(self, voice: BinaryIO, grp_id: int) -> Audio:
        return await self._highway.upload_voice(voice, gid=grp_id)

    async def get_grp_msg(
        self, grp_id: int, start: int, end: int = 0, filter_deleted_msg=True
    ) -> List[GroupMessage]:
        if not end:
            end = start
        payload = GetGrpMsgRsp.decode(
            (
                await self.send_uni_packet(
                    "trpc.msg.register_proxy.RegisterProxy.SsoGetGroupMsg",
                    PBGetGrpMsgRequest.build(grp_id, start, end).encode(),
                )
            ).data
        ).body

        assert (
            payload.grp_id == grp_id
            and payload.start_seq == start
            and payload.end_seq == end
        ), "return args not matched"

        rsp = [parse_grp_msg(MsgPushBody.decode(i)) for i in payload.elems]
        if filter_deleted_msg:
            return [*filter(lambda msg: msg.rand != -1, rsp)]
        return rsp

    async def recall_grp_msg(self, grp_id: int, seq: int):
        payload = await self.send_uni_packet(
            "trpc.msg.msg_svc.MsgService.SsoGroupRecallMsg",
            PBGroupRecallRequest.build(grp_id, seq).encode(),
        )
        result = proto_decode(payload.data)
        if result[2] != b"Success":
            raise AssertionError(result)

    async def rename_grp_name(self, grp_id: int, name: str) -> int:  # not test
        return (
            await self.send_oidb_svc(
                0x89A, 15, PBGroupRenameRequest.build(grp_id, name).encode()
            )
        ).ret_code

    async def rename_grp_member(self, grp_id: int, target_uid: str, name: str):  # fixme
        rsp = await self.send_oidb_svc(
            0x8FC,
            3,
            PBRenameMemberRequest.build(grp_id, target_uid, name).encode(),
            True,
        )
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, rsp.err_msg)

    async def leave_grp(self, grp_id: int) -> int:  # not test
        return (
            await self.send_oidb_svc(
                0x1097, 1, PBLeaveGroupRequest.build(grp_id).encode()
            )
        ).ret_code

    async def send_nudge(self, uin: int, grp_id: int = 0) -> int:
        """grp_id=0 when send to friend"""
        return (
            await self.send_oidb_svc(
                0xED3,
                1,
                SendNudge(
                    to_dst1=uin,
                    to_grp=grp_id if grp_id else None,
                    to_uin=uin if not grp_id else None,
                ).encode(),
            )
        ).ret_code

    async def set_essence(self, grp_id: int, seq: int, rand: int, is_remove=False):
        rsp = SetEssenceRsp.decode(
            (
                await self.send_oidb_svc(
                    0xEAC,
                    1 if not is_remove else 2,
                    PBSetEssence(grp_id=grp_id, seq=seq, rand=rand).encode(),
                )
            ).data
        )
        if rsp:
            raise AssertionError(rsp.code, rsp.msg)

    async def set_mute_grp(self, grp_id: int, enable: bool):
        rsp = await self.send_oidb_svc(
            0x89A,
            0,
            PBGroupMuteRequest.build(grp_id, 0xFFFFFFFF if enable else 0).encode(),
        )
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, rsp.err_msg)

    async def fetch_grp_request(self, count=20) -> FetchGroupResponse:
        rsp = FetchGroupResponse.decode(
            (
                await self.send_oidb_svc(
                    0x10C0, 1, PBFetchGroupRequest(count=count).encode()
                )
            ).data
        )
        return rsp

    async def set_grp_request(
        self, grp_id: int, grp_req_seq: int, ev_type: int, action: int, reason=""
    ):
        """
        grp_req_seq: from fetch_grp_request
        action: 1 for accept; 2 for reject; 3 for ignore
        """
        rsp = await self.send_oidb_svc(
            0x10C8,
            1,
            PBHandleGroupRequest.build(
                action, grp_req_seq, ev_type, grp_id, reason
            ).encode(),
        )
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, rsp.err_msg)
