from typing import Union, Optional

from lagrange.utils.binary.protobuf import ProtoStruct, proto_field


class GetGrpMsgReqBody(ProtoStruct):
    grp_id: int = proto_field(1)
    start_seq: int = proto_field(2)
    end_seq: int = proto_field(3)


class PBGetGrpMsgRequest(ProtoStruct):
    body: GetGrpMsgReqBody = proto_field(1)
    direction: bool = proto_field(2, default=True)

    @classmethod
    def build(
        cls, grp_id: int, start_seq: int, end_seq: int, direction=True
    ) -> "PBGetGrpMsgRequest":
        return cls(
            body=GetGrpMsgReqBody(grp_id=grp_id, start_seq=start_seq, end_seq=end_seq),
            direction=direction,
        )


class RecallRequestF3(ProtoStruct):
    seq: int = proto_field(1)
    # rand: int = proto_field(2)
    field3: int = proto_field(3, default=0)


class PBGroupRecallRequest(ProtoStruct):
    type: int = proto_field(1, default=1)
    grp_id: int = proto_field(2)
    field3: RecallRequestF3 = proto_field(3)
    field4: dict = proto_field(4, default={1: 0})

    @classmethod
    def build(cls, grp_id: int, seq: int) -> "PBGroupRecallRequest":
        return PBGroupRecallRequest(grp_id=grp_id, field3=RecallRequestF3(seq=seq))


class RenameRequestF2(ProtoStruct):
    name: str = proto_field(3)


class PBGroupRenameRequest(ProtoStruct):
    grp_id: int = proto_field(1)
    rename_f2: RenameRequestF2 = proto_field(2)

    @classmethod
    def build(cls, grp_id: int, name: str) -> "PBGroupRenameRequest":
        return cls(grp_id=grp_id, rename_f2=RenameRequestF2(name=name))


class RenameMemberRequestF3(ProtoStruct):
    uid: str = proto_field(1)
    name: str = proto_field(8)


class PBRenameMemberRequest(ProtoStruct):
    grp_id: int = proto_field(1)
    rename_f3: RenameMemberRequestF3 = proto_field(3)

    @classmethod
    def build(cls, grp_id: int, target_uid: str, name: str) -> "PBRenameMemberRequest":
        return cls(
            grp_id=grp_id, rename_f3=RenameMemberRequestF3(uid=target_uid, name=name)
        )


class PBLeaveGroupRequest(ProtoStruct):
    grp_id: int = proto_field(1)

    @classmethod
    def build(cls, grp_id: int) -> "PBLeaveGroupRequest":
        return cls(grp_id=grp_id)


class GetGrpMsgRspBody(ProtoStruct):
    grp_id: int = proto_field(3)
    start_seq: int = proto_field(4)
    end_seq: int = proto_field(5)
    elems: list[bytes] = proto_field(6, default=[])


class GetGrpMsgRsp(ProtoStruct):
    body: GetGrpMsgRspBody = proto_field(3)


class PBSetEssence(ProtoStruct):
    grp_id: int = proto_field(1)
    seq: int = proto_field(2)
    rand: int = proto_field(3)


class SetEssenceRsp(ProtoStruct):
    msg: str = proto_field(1)
    code: int = proto_field(10)


class GroupMuteBody(ProtoStruct):
    duration: int = proto_field(17)


class PBGroupMuteRequest(ProtoStruct):
    grp_id: int = proto_field(1)
    body: GroupMuteBody = proto_field(2)

    @classmethod
    def build(cls, grp_id: int, duration: int) -> "PBGroupMuteRequest":
        return cls(grp_id=grp_id, body=GroupMuteBody(duration=duration))


class PBFetchGroupRequest(ProtoStruct):
    count: int = proto_field(1, default=20)
    f2: int = proto_field(2, default=0)


class RspGroup(ProtoStruct):
    grp_id: int = proto_field(1)
    grp_name: str = proto_field(2)


class RspUser(ProtoStruct):
    uid: str = proto_field(1)
    name: str = proto_field(2)


class FetchGrpRspBody(ProtoStruct):
    seq: int = proto_field(1)
    event_type: int = proto_field(2)
    state: Optional[int] = proto_field(3, default=None)
    group: RspGroup = proto_field(4)
    target: RspUser = proto_field(5)
    invitor: Optional[RspUser] = proto_field(6, default=None)
    operator: Optional[RspUser] = proto_field(7, default=None)
    comment: str = proto_field(9, default="")


class FetchGroupResponse(ProtoStruct):
    requests: list[FetchGrpRspBody] = proto_field(1)
    latest_seq: int = proto_field(3)


class HandleGrpReqBody(ProtoStruct):
    seq: int = proto_field(1)
    event_type: int = proto_field(2)
    grp_id: int = proto_field(3)
    message: str = proto_field(4)


class PBHandleGroupRequest(ProtoStruct):
    action: int = proto_field(1)
    body: HandleGrpReqBody = proto_field(2)

    @classmethod
    def build(
        cls, action: int, seq: int, event_type: int, grp_id: int, message: str
    ) -> "PBHandleGroupRequest":
        return cls(
            action=action,
            body=HandleGrpReqBody(
                seq=seq, event_type=event_type, grp_id=grp_id, message=message
            ),
        )


class PBSendGrpReactionReq(ProtoStruct):
    grp_id: int = proto_field(2)
    seq: int = proto_field(3)
    content: str = proto_field(4)
    type: int = proto_field(5)
    f6: int = proto_field(6, default=0)
    f7: int = proto_field(7, default=0)

    @classmethod
    def build(
        cls, grp_id: int, seq: int, content: Union[str, int]
    ) -> "PBSendGrpReactionReq":
        return cls(
            grp_id=grp_id,
            seq=seq,
            content=str(content) if isinstance(content, int) else str(ord(content)),
            type=1 if isinstance(content, int) else 2,
        )


class GroupMuteMemberReqBody(ProtoStruct):
    uid: str = proto_field(1)
    duration: int = proto_field(2)


class PBGroupMuteMemberRequest(ProtoStruct):
    grp_id: int = proto_field(1)
    type: int = proto_field(2, default=1)
    body: GroupMuteMemberReqBody = proto_field(3)

    @classmethod
    def build(cls, grp_id: int, uid: str, duration: int) -> "PBGroupMuteMemberRequest":
        return cls(
            grp_id=grp_id, body=GroupMuteMemberReqBody(uid=uid, duration=duration)
        )


# class PBGroupKickMemberRequest(ProtoStruct):
#     grp_id: int = proto_field(1)
#     target_uid: str = proto_field(3)
#     permanent: bool = proto_field(4)
#     f5: str = proto_field(5, default="")
#
#     @classmethod
#     def build(
#             cls, grp_id: int, target_uid: str, permanent: bool
#     ) -> "PBGroupKickMemberRequest":
#         return cls(
#             grp_id=grp_id,
#             target_uid=target_uid,
#             permanent=permanent
#         )


class GroupKickMemberReqBody(ProtoStruct):
    f1: int = proto_field(1, default=5)
    uin: int = proto_field(2)
    permanent: bool = proto_field(3)


class PBGroupKickMemberRequest(ProtoStruct):
    grp_id: int = proto_field(1)
    body: GroupKickMemberReqBody = proto_field(2)

    @classmethod
    def build(
        cls, grp_id: int, uin: int, permanent: bool
    ) -> "PBGroupKickMemberRequest":
        return cls(
            grp_id=grp_id, body=GroupKickMemberReqBody(uin=uin, permanent=permanent)
        )


# # group_member_card.get_group_member_card_info
# class PBGetMemberCardReq(ProtoStruct):
#     grp_id: int = proto_field(1)
#     uin: int = proto_field(2)
#     f3: int = proto_field(3, default=1)
#     f4: int = proto_field(4, default=1)
#     f5: int = proto_field(5, default=1)
#
#     @classmethod
#     def build(cls, grp_id: int, uin: int) -> "PBGetMemberCardReq":
#         return cls(
#             grp_id=grp_id,
#             uin=uin,
#         )
#
#
# class GetMemberCardRspBody(ProtoStruct, debug=True):
#     uin: int = proto_field(1)
#     nickname: str = proto_field(8)
#     region_name: str = proto_field(10)
#     name: str = proto_field(11)
#     age: int = proto_field(12)
#     level_name: str = proto_field(13)
#     joined_time: int = proto_field(14)
#     timestamp: int = proto_field(15)  # ?
#     level: dict = proto_field(41, default={})  # level_num: level[2]
#
#
# class GetMemberCardRsp(ProtoStruct):
#     grp_id: int = proto_field(1)
#     f2: int = proto_field(2)  # 2
#     body: GetMemberCardRspBody = proto_field(3)


class AccountInfo(ProtoStruct):
    uid: str = proto_field(2)
    uin: Optional[int] = proto_field(4, default=None)


class PBGetGrpMemberInfoReq(ProtoStruct):
    grp_id: int = proto_field(1)
    f2: int = proto_field(2)
    f3: int = proto_field(3)
    fetch_list: bytes = proto_field(4)  # dict[int, 1]
    account: Optional[AccountInfo] = proto_field(5, default=None)
    next_key: Optional[bytes] = proto_field(15, default=None)  # base64(pb)

    @classmethod
    def build(cls, grp_id: int, uid="", next_key: Optional[str] = None) -> "PBGetGrpMemberInfoReq":
        assert not (uid and next_key), "invalid arguments"
        if uid:
            account = AccountInfo(uid=uid)
            f2 = 3
            f3 = 0
        else:  # member_list
            account = None
            f2 = 5
            f3 = 2
        return cls(
            grp_id=grp_id,
            f2=f2,
            f3=f3,
            fetch_list=bytes.fromhex(
                "500158016001680170017801800101a00101a00601a80601c00601c80601c00c01"
            ),  # 10-16, 20, 100, 101, 104, 105, 200
            account=account,
            next_key=next_key,
        )


class MemberInfoName(ProtoStruct):
    string: str = proto_field(2)


class MemberInfoLevel(ProtoStruct):
    num: int = proto_field(2)


class GetGrpMemberInfoRspBody(ProtoStruct):
    account: AccountInfo = proto_field(1)
    nickname: str = proto_field(10, default="")
    name: Optional[MemberInfoName] = proto_field(11, default=None)  # if none? not set
    level: Optional[MemberInfoLevel] = proto_field(12, default=None)  # if none? retry
    permission: int = proto_field(13)  # 2: owner, 1: others
    f14: Optional[int] = proto_field(14, default=None)
    f15: Optional[int] = proto_field(15, default=None)
    f16: Optional[int] = proto_field(16, default=None)
    # f20: int = proto_field(20)  # always 1
    joined_time: int = proto_field(100)
    last_seen: int = proto_field(101)

    is_admin: bool = proto_field(103, default=False)  # not owner
    f104: Optional[int] = proto_field(104, default=None)
    f105: Optional[int] = proto_field(105, default=None)
    f200: Optional[int] = proto_field(200, default=None)

    @property
    def is_owner(self) -> bool:
        return not self.is_admin and self.permission == 2


class GetGrpMemberInfoRsp(ProtoStruct):
    grp_id: int = proto_field(1)
    body: list[GetGrpMemberInfoRspBody] = proto_field(2)
    next_key: Optional[bytes] = proto_field(15, default=None)  # base64(pb)


class GetGrpListReqBody(ProtoStruct):
    cfg1: bytes = proto_field(1)
    cfg2: bytes = proto_field(2)
    cfg3: bytes = proto_field(3)


class PBGetGrpListRequest(ProtoStruct):
    body: GetGrpListReqBody = proto_field(1)

    @classmethod
    def build(cls) -> "PBGetGrpListRequest":
        return cls(
            body=GetGrpListReqBody(
                cfg1=bytes.fromhex(
                    "0801100118012001280140014801500158016001680170017801800101"
                    "880101900101980101a00101b00101b80101c00101c80101d00101d801"
                    "01e00101e80101f00101f80101800201c8b80201d0b80201d8b80201"
                ),  # 1-5, 8-20, 22-32, 5001-5003
                cfg2=bytes.fromhex("08011001180120012801300138014001"),  # 1-8
                cfg3=bytes.fromhex("28013001"),  # 5-6
            )
        )


class GrpInfoBasic(ProtoStruct):
    owner: AccountInfo = proto_field(1)  # uid only
    create_time: int = proto_field(2)
    max_members: int = proto_field(3)
    now_members: int = proto_field(4)
    grp_name: str = proto_field(5)
    introduce: Optional[str] = proto_field(18, default=None)
    question: Optional[str] = proto_field(19, default=None)
    recent_notice: Optional[str] = proto_field(30, default=None)  # 30 chars


class GrpInfoOther(ProtoStruct):
    create_time: int = proto_field(1)  # ?
    upgrade_time: Optional[int] = proto_field(4, default=None)  # when upgrade grp size?
    f5: Optional[int] = proto_field(5, default=None)  # unknown


class GrpInfo(ProtoStruct):
    grp_id: int = proto_field(3)
    info: GrpInfoBasic = proto_field(4)
    other: GrpInfoOther = proto_field(5)


class GetGrpListResponse(ProtoStruct):
    grp_list: list[GrpInfo] = proto_field(2, default=[])


class PBGetInfoFromUidReq(ProtoStruct):
    uid: list[str] = proto_field(1)
    cfg: bytes = proto_field(
        3,
        default=bytes.fromhex(
            "08a29c0108a39c0108a49c0108a59c0108a69c0108a79c0108a99c"
            "0108ab9c0108b49c0108b59c0108ba9c0108bf9c0108c59c011802"
        ),
    )


class GetInfoRspF1(ProtoStruct):
    type: int = proto_field(1)
    value: int = proto_field(2)


class GetInfoRspF2(ProtoStruct):
    type: int = proto_field(1)
    value: bytes = proto_field(2)

    @property
    def to_str(self) -> str:
        return self.value.decode()


class GetInfoRspField(ProtoStruct, debug=True):
    int_t: list[GetInfoRspF1] = proto_field(1, default=[])
    str_t: list[GetInfoRspF2] = proto_field(2, default=[])


class GetInfoRspBody(ProtoStruct):
    uid: str = proto_field(1)
    fields: GetInfoRspField = proto_field(2)


class GetInfoFromUidRsp(ProtoStruct):
    body: list[GetInfoRspBody] = proto_field(1)
