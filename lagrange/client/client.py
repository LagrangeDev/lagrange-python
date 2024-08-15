import os
import struct
import asyncio
from io import BytesIO
from typing import (
    BinaryIO,
    Callable,
    Coroutine,
    List,
    Optional,
    Union,
    overload,
    Literal,
)

from lagrange.info import AppInfo, DeviceInfo, SigInfo
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.message.send import SendMsgRsp
from lagrange.pb.service.comm import SendNudge
from lagrange.pb.service.friend import (
    GetFriendListRsp,
    GetFriendListUin,
    PBGetFriendListRequest,
    propertys,
)
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
    PBSendGrpReactionReq,
    PBSetEssence,
    PBGroupKickMemberRequest,
    # PBGetMemberCardReq,
    # GetMemberCardRsp,
    PBGetGrpListRequest,
    GetGrpListResponse,
    PBGetGrpMemberInfoReq,
    GetGrpMemberInfoRsp,
    SetEssenceRsp,
    GetInfoFromUidRsp,
    PBGetInfoFromUidReq,
)
from lagrange.pb.service.oidb import OidbRequest, OidbResponse
from lagrange.pb.highway.comm import IndexNode
from lagrange.utils.binary.protobuf import proto_decode, proto_encode
from lagrange.utils.log import log
from lagrange.utils.operator import timestamp

from qrcode.main import QRCode

from .base import BaseClient
from .event import Events
from .events.group import GroupMessage
from .events.service import ClientOnline, ClientOffline
from .highway import HighWaySession
from .message.decoder import parse_grp_msg
from .message.elems import Audio, Image
from .message.encoder import build_message
from .message.types import Element
from .models import UserInfo, BotFriend
from .server_push import PushDeliver, bind_services
from .wtlogin.sso import SSOPacket


class Client(BaseClient):
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
        super().__init__(uin, app_info, device_info, sig_info, sign_provider, use_ipv6)

        self._events = Events()
        self._push_deliver = PushDeliver(self)
        self._highway = HighWaySession(self)
        bind_services(self._push_deliver)

    @property
    def events(self) -> Events:
        return self._events

    @property
    def push_deliver(self) -> PushDeliver:
        return self._push_deliver

    async def register(self) -> bool:
        if await super().register():
            self._events.emit(ClientOnline(), self)
            return True
        self._events.emit(ClientOffline(recoverable=False), self)
        return False

    async def _disconnect_cb(self, recover: bool):
        self._events.emit(ClientOffline(recoverable=recover), self)
        await super()._disconnect_cb(recover)

    async def easy_login(self) -> bool:
        if self._sig.temp_pwd:  # EasyLogin
            await self._key_exchange()

            rsp = await self.token_login(self._sig.temp_pwd)
            if rsp.successful:
                return await self.register()
            return False
        else:
            raise AssertionError("siginfo not found, you must login first")

    async def login(
        self, password: str = "", qrcode_path: Optional[str] = None
    ) -> bool:
        try:
            if self._sig.temp_pwd:
                rsp = await self.easy_login()
                if rsp:
                    return True
        except Exception as e:
            log.login.error("EasyLogin fail", exc_info=e)

        if password:  # TODO: PasswordLogin, WIP
            await self._key_exchange()

            while True:
                rsp = await self.password_login(password)
                if rsp.successful:
                    return await self.register()
                elif rsp.captcha_verify:
                    log.root.warning("captcha verification required")
                    self.submit_login_captcha(
                        ticket=input("ticket?->"), rand_str=input("rand_str?->")
                    )
                else:
                    log.root.error(f"Unhandled exception raised: {rsp.name}")
        else:  # QrcodeLogin
            ret = await self.fetch_qrcode()
            if isinstance(ret, int):
                log.root.error(f"fetch qrcode fail: {ret}")
            else:
                png, _link = ret
                if qrcode_path:
                    log.root.info(f"save qrcode to '{qrcode_path}'")
                    with open(qrcode_path, "wb") as f:
                        f.write(png)
                else:
                    qr = QRCode()
                    qr.add_data(_link)
                    log.root.info("Please scan the qrcode below")
                    qr.print_ascii()
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
            log.network.error(
                f"OidbSvc(0x{cmd:X}_{sub_cmd}) return an error: ({rsp.ret_code}){rsp.err_msg}"
            )
        return rsp

    async def push_handler(self, sso: SSOPacket):
        if rsp := await self._push_deliver.execute(sso.cmd, sso):
            self._events.emit(rsp, self)

    async def _send_msg_raw(self, pb: dict, *, grp_id=0, uid="") -> SendMsgRsp:
        seq = self.seq + 1
        sendto = {}
        if not grp_id:  # friend
            assert uid, "uid must be set"
            sendto[1] = {2: uid}
        elif grp_id:  # grp
            sendto[2] = {1: grp_id}
        elif uid and grp_id:  # temp msg, untest
            assert uid or grp_id, "uid and grp_id"
            sendto[3] = {1: grp_id, 2: uid}
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
            body[6] = {1: timestamp()}

        packet = await self.send_uni_packet("MessageSvc.PbSendMsg", proto_encode(body))
        return SendMsgRsp.decode(packet.data)

    async def send_grp_msg(self, msg_chain: List[Element], grp_id: int) -> int:
        result = await self._send_msg_raw(
            {1: build_message(msg_chain).encode()}, grp_id=grp_id
        )
        if result.ret_code:
            raise AssertionError(result.ret_code, result.err_msg)
        return result.seq

    async def send_friend_msg(self, msg_chain: List[Element], uid: str) -> int:
        result = await self._send_msg_raw(
            {1: build_message(msg_chain).encode()}, uid=uid
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

    async def upload_friend_image(
        self, image: BinaryIO, uid: str, is_emoji=False
    ) -> Image:
        img = await self._highway.upload_image(image, uid=uid)
        if is_emoji:
            img.is_emoji = True
        return img

    async def upload_grp_audio(self, voice: BinaryIO, grp_id: int) -> Audio:
        return await self._highway.upload_voice(voice, gid=grp_id)

    async def upload_friend_audio(self, voice: BinaryIO, uid: str) -> Audio:
        return await self._highway.upload_voice(voice, uid=uid)

    async def down_grp_audio(self, audio: Audio, grp_id: int) -> BytesIO:
        return await self._highway.download_audio(audio, gid=grp_id)

    async def down_friend_audio(self, audio: Audio) -> BytesIO:
        return await self._highway.download_audio(audio, uid=self.uid)

    async def fetch_image_url(
        self, bus_type: Literal[10, 20], node: "IndexNode", uid=None, gid=None
    ):
        if bus_type == 10:
            return await self._get_pri_img_url(uid, node)
        elif bus_type == 20:
            return await self._get_grp_img_url(gid, node)
        else:
            raise ValueError("bus_type must be 10 or 20")

    async def _get_grp_img_url(self, grp_id: int, node: "IndexNode") -> str:
        return await self._highway.get_grp_img_url(grp_id=grp_id, node=node)

    async def _get_pri_img_url(self, uid: str, node: "IndexNode") -> str:
        return await self._highway.get_pri_img_url(uid=uid, node=node)

    async def get_grp_list(self) -> GetGrpListResponse:
        rsp = await self.send_oidb_svc(0xFE5, 2, PBGetGrpListRequest.build().encode())
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, rsp.err_msg)
        return GetGrpListResponse.decode(rsp.data)

    # RIP: server not impl
    # async def get_grp_member_card(self, grp_id: int, uin: int) -> GetMemberCardRsp:
    #     return GetMemberCardRsp.decode(
    #         (
    #             await self.send_uni_packet(
    #                 "group_member_card.get_group_member_card_info",
    #                 PBGetMemberCardReq.build(grp_id, uin).encode(),
    #             )
    #         ).data
    #     )

    async def get_grp_member_info(self, grp_id: int, uid: str) -> GetGrpMemberInfoRsp:
        return GetGrpMemberInfoRsp.decode(
            (
                await self.send_oidb_svc(
                    0xFE7, 4, PBGetGrpMemberInfoReq.build(grp_id, uid=uid).encode()
                )
            ).data
        )

    async def get_grp_members(
        self, grp_id: int, next_key: Optional[str] = None
    ) -> GetGrpMemberInfoRsp:
        """
        500 members per request,
        get next page: fill 'next_key' from GetGrpMemberInfoRsp.next_key
        """
        return GetGrpMemberInfoRsp.decode(
            (
                await self.send_oidb_svc(
                    0xFE7,
                    4,
                    PBGetGrpMemberInfoReq.build(grp_id, next_key=next_key).encode(),
                )
            ).data
        )

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

        rsp = list(
            await asyncio.gather(
                *[parse_grp_msg(self, MsgPushBody.decode(i)) for i in payload.elems]
            )
        )
        if filter_deleted_msg:
            return [*filter(lambda msg: msg.rand != -1, rsp)]
        return rsp

    async def get_friend_list(self):
        nextuin_cache: List[GetFriendListUin] = []
        rsp: List[BotFriend] = []
        frist_send = GetFriendListRsp.decode(
            (await self.send_oidb_svc(0xFD4, 1, PBGetFriendListRequest().encode())).data
        )
        properties: Optional[dict] = None
        if frist_send.next:
            nextuin_cache.append(frist_send.next)
        for raw in frist_send.friend_list:
            for j in raw.additional:
                if j.type != 1:
                    continue
                properties = propertys(j.layer1.properties)
                break
            if properties is not None:
                rsp.append(
                    BotFriend(
                        raw.uin,
                        raw.uid,
                        properties.get(20002),
                        properties.get(103),
                        properties.get(102),
                        properties.get(27394),
                    )
                )

        while nextuin_cache:
            next = GetFriendListRsp.decode(
                (
                    await self.send_oidb_svc(
                        0xFD4,
                        1,
                        PBGetFriendListRequest(next_uin=nextuin_cache.pop()).encode(),
                    )
                ).data
            )
            for raw in next.friend_list:
                for j in raw.additional:
                    properties = propertys(j.layer1.properties)
                if properties is not None:
                    rsp.append(
                        BotFriend(
                            raw.uin,
                            raw.uid,
                            properties.get(20002),
                            properties.get(103),
                            properties.get(102),
                            properties.get(27394),
                        )
                    )
            if next.next:
                nextuin_cache.append(next.next)

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

    async def kick_grp_member(self, grp_id: int, uin: int, permanent=False):
        rsp = await self.send_oidb_svc(
            0x8A0,
            0,
            PBGroupKickMemberRequest.build(grp_id, uin, permanent).encode(),
            True,
        )
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, str(rsp.err_msg))

    async def send_grp_reaction(
        self, grp_id: int, msg_seq: int, content: Union[str, int], is_cancel=False
    ) -> None:
        if isinstance(content, str):
            assert len(content) == 1, "content must be a emoji"
        rsp = await self.send_oidb_svc(
            0x9082,
            1 + is_cancel,
            PBSendGrpReactionReq.build(grp_id, msg_seq, content).encode(),
        )
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, str(rsp.err_msg))

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

    # async def set_mute_member(self, grp_id: int, uin: int, duration: int):
    #     rsp = await self.send_oidb_svc(
    #         0x1253,
    #         1,
    #         PBGroupMuteMemberRequest.build(grp_id, uid, duration).encode(),
    #         True
    #     )
    #     if rsp.ret_code:
    #         raise AssertionError(rsp.ret_code, rsp.err_msg)

    async def set_mute_member(self, grp_id: int, uin: int, duration: int):
        rsp = await self.send_oidb_svc(
            0x570, 8, struct.pack(">IBHII", grp_id, 0x20, 1, uin, duration)
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

    @overload
    async def get_user_info(self, uid: str) -> UserInfo: ...

    @overload
    async def get_user_info(self, uid: List[str]) -> List[UserInfo]: ...

    async def get_user_info(
        self, uid: Union[str, List[str]]
    ) -> Union[UserInfo, List[UserInfo]]:
        if isinstance(uid, str):
            uid = [uid]
        rsp = GetInfoFromUidRsp.decode(
            (
                await self.send_oidb_svc(
                    0xFE1, 8, PBGetInfoFromUidReq(uid=uid).encode()
                )
            ).data
        )
        if not rsp.body:
            raise AssertionError("Empty response")
        elif len(rsp.body) == 1:
            return UserInfo.from_pb(rsp.body[0])
        else:
            return [UserInfo.from_pb(body) for body in rsp.body]
