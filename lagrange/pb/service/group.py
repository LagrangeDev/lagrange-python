from typing import Union

from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class GetGrpMsgReqBody(ProtoStruct):
    grp_id: int = ProtoField(1)
    start_seq: int = ProtoField(2)
    end_seq: int = ProtoField(3)


class PBGetGrpMsgRequest(ProtoStruct):
    body: GetGrpMsgReqBody = ProtoField(1)
    direction: bool = ProtoField(2, True)

    @classmethod
    def build(
        cls, grp_id: int, start_seq: int, end_seq: int, direction=True
    ) -> "PBGetGrpMsgRequest":
        return cls(
            body=GetGrpMsgReqBody(grp_id=grp_id, start_seq=start_seq, end_seq=end_seq),
            direction=direction,
        )


class RecallRequestF3(ProtoStruct):
    seq: int = ProtoField(1)
    # rand: int = ProtoField(2)
    field3: int = ProtoField(3, 0)


class PBGroupRecallRequest(ProtoStruct):
    type: int = ProtoField(1, 1)
    grp_id: int = ProtoField(2)
    field3: RecallRequestF3 = ProtoField(3)
    field4: dict = ProtoField(4, {1: 0})

    @classmethod
    def build(cls, grp_id: int, seq: int) -> "PBGroupRecallRequest":
        return PBGroupRecallRequest(grp_id=grp_id, field3=RecallRequestF3(seq=seq))


class RenameRequestF2(ProtoStruct):
    name: str = ProtoField(3)


class PBGroupRenameRequest(ProtoStruct):
    grp_id: int = ProtoField(1)
    rename_f2: RenameRequestF2 = ProtoField(2)

    @classmethod
    def build(cls, grp_id: int, name: str) -> "PBGroupRenameRequest":
        return cls(grp_id=grp_id, rename_f2=RenameRequestF2(name=name))


class RenameMemberRequestF3(ProtoStruct):
    uid: str = ProtoField(1)
    name: str = ProtoField(8)


class PBRenameMemberRequest(ProtoStruct):
    grp_id: int = ProtoField(1)
    rename_f3: RenameMemberRequestF3 = ProtoField(3)

    @classmethod
    def build(cls, grp_id: int, target_uid: str, name: str) -> "PBRenameMemberRequest":
        return cls(
            grp_id=grp_id, rename_f3=RenameMemberRequestF3(uid=target_uid, name=name)
        )


class PBLeaveGroupRequest(ProtoStruct):
    grp_id: int = ProtoField(1)

    @classmethod
    def build(cls, grp_id: int) -> "PBLeaveGroupRequest":
        return cls(grp_id=grp_id)


class GetGrpMsgRspBody(ProtoStruct):
    grp_id: int = ProtoField(3)
    start_seq: int = ProtoField(4)
    end_seq: int = ProtoField(5)
    elems: list[bytes] = ProtoField(6, [])


class GetGrpMsgRsp(ProtoStruct):
    body: GetGrpMsgRspBody = ProtoField(3)


class PBSetEssence(ProtoStruct):
    grp_id: int = ProtoField(1)
    seq: int = ProtoField(2)
    rand: int = ProtoField(3)


class SetEssenceRsp(ProtoStruct):
    msg: str = ProtoField(1)
    code: int = ProtoField(10)


class GroupMuteBody(ProtoStruct):
    duration: int = ProtoField(17)


class PBGroupMuteRequest(ProtoStruct):
    grp_id: int = ProtoField(1)
    body: GroupMuteBody = ProtoField(2)

    @classmethod
    def build(cls, grp_id: int, duration: int) -> "PBGroupMuteRequest":
        return cls(grp_id=grp_id, body=GroupMuteBody(duration=duration))


class PBFetchGroupRequest(ProtoStruct):
    count: int = ProtoField(1, 20)
    f2: int = ProtoField(2, 0)


class RspGroup(ProtoStruct):
    grp_id: int = ProtoField(1)
    grp_name: str = ProtoField(2)


class RspUser(ProtoStruct):
    uid: str = ProtoField(1)
    name: str = ProtoField(2)


class FetchGrpRspBody(ProtoStruct):
    seq: int = ProtoField(1)
    event_type: int = ProtoField(2)
    state: int = ProtoField(3, None)
    group: RspGroup = ProtoField(4)
    target: RspUser = ProtoField(5)
    invitor: RspUser = ProtoField(6, None)
    operator: RspUser = ProtoField(7, None)
    comment: str = ProtoField(9, "")


class FetchGroupResponse(ProtoStruct):
    requests: list[FetchGrpRspBody] = ProtoField(1)
    latest_seq: int = ProtoField(3)


class HandleGrpReqBody(ProtoStruct):
    seq: int = ProtoField(1)
    event_type: int = ProtoField(2)
    grp_id: int = ProtoField(3)
    message: str = ProtoField(4)


class PBHandleGroupRequest(ProtoStruct):
    action: int = ProtoField(1)
    body: HandleGrpReqBody = ProtoField(2)

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
    grp_id: int = ProtoField(2)
    seq: int = ProtoField(3)
    content: str = ProtoField(4)
    type: int = ProtoField(5)
    f6: int = ProtoField(6, 0)
    f7: int = ProtoField(7, 0)

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
    uid: str = ProtoField(1)
    duration: int = ProtoField(2)


class PBGroupMuteMemberRequest(ProtoStruct):
    grp_id: int = ProtoField(1)
    type: int = ProtoField(2, 1)
    body: GroupMuteMemberReqBody = ProtoField(3)

    @classmethod
    def build(cls, grp_id: int, uid: str, duration: int) -> "PBGroupMuteMemberRequest":
        return cls(
            grp_id=grp_id, body=GroupMuteMemberReqBody(uid=uid, duration=duration)
        )


# class PBGroupKickMemberRequest(ProtoStruct):
#     grp_id: int = ProtoField(1)
#     target_uid: str = ProtoField(3)
#     permanent: bool = ProtoField(4)
#     f5: str = ProtoField(5, "")
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
    f1: int = ProtoField(1, 5)
    uin: int = ProtoField(2)
    permanent: bool = ProtoField(3)


class PBGroupKickMemberRequest(ProtoStruct):
    grp_id: int = ProtoField(1)
    body: GroupKickMemberReqBody = ProtoField(2)

    @classmethod
    def build(
        cls, grp_id: int, uin: int, permanent: bool
    ) -> "PBGroupKickMemberRequest":
        return cls(
            grp_id=grp_id, body=GroupKickMemberReqBody(uin=uin, permanent=permanent)
        )


# # group_member_card.get_group_member_card_info
# class PBGetMemberCardReq(ProtoStruct):
#     grp_id: int = ProtoField(1)
#     uin: int = ProtoField(2)
#     f3: int = ProtoField(3, 1)
#     f4: int = ProtoField(4, 1)
#     f5: int = ProtoField(5, 1)
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
#     uin: int = ProtoField(1)
#     nickname: str = ProtoField(8)
#     region_name: str = ProtoField(10)
#     name: str = ProtoField(11)
#     age: int = ProtoField(12)
#     level_name: str = ProtoField(13)
#     joined_time: int = ProtoField(14)
#     timestamp: int = ProtoField(15)  # ?
#     level: dict = ProtoField(41, {})  # level_num: level[2]
#
#
# class GetMemberCardRsp(ProtoStruct):
#     grp_id: int = ProtoField(1)
#     f2: int = ProtoField(2)  # 2
#     body: GetMemberCardRspBody = ProtoField(3)


class AccountInfo(ProtoStruct):
    uid: str = ProtoField(2)
    uin: int = ProtoField(4, None)


class PBGetGrpMemberInfoReq(ProtoStruct):
    grp_id: int = ProtoField(1)
    f2: int = ProtoField(2)
    f3: int = ProtoField(3)
    fetch_list: bytes = ProtoField(4)  # dict[int, 1]
    account: AccountInfo = ProtoField(5, None)
    next_key: bytes = ProtoField(15, None)  # base64(pb)

    @classmethod
    def build(cls, grp_id: int, uid="", next_key=None) -> "PBGetGrpMemberInfoReq":
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
                "500158016001680170017801800101a00" "101a00601a80601c00601c80601c00c01"
            ),  # 10-16, 20, 100, 101, 104, 105, 200
            account=account,
            next_key=next_key,
        )


class MemberInfoName(ProtoStruct):
    string: str = ProtoField(2)


class MemberInfoLevel(ProtoStruct):
    num: int = ProtoField(2)


class GetGrpMemberInfoRspBody(ProtoStruct):
    account: AccountInfo = ProtoField(1)
    nickname: str = ProtoField(10, "")
    name: MemberInfoName = ProtoField(11, None)  # if none? not set
    level: MemberInfoLevel = ProtoField(12, None)  # if none? retry
    permission: int = ProtoField(13)  # ?
    is_admin: int = ProtoField(20)
    joined_time: int = ProtoField(100)
    last_seen: int = ProtoField(101)

    f104: int = ProtoField(104, None)
    f105: int = ProtoField(105, None)
    f200: int = ProtoField(200, None)


class GetGrpMemberInfoRsp(ProtoStruct):
    grp_id: int = ProtoField(1)
    body: list[GetGrpMemberInfoRspBody] = ProtoField(2)
    next_key: bytes = ProtoField(15, None)  # base64(pb)


class GetGrpListReqBody(ProtoStruct):
    cfg1: bytes = ProtoField(1)
    cfg2: bytes = ProtoField(2)
    cfg3: bytes = ProtoField(3)


class PBGetGrpListRequest(ProtoStruct):
    body: GetGrpListReqBody = ProtoField(1)

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
    owner: AccountInfo = ProtoField(1)  # uid only
    create_time: int = ProtoField(2)
    max_members: int = ProtoField(3)
    now_members: int = ProtoField(4)
    grp_name: str = ProtoField(5)
    introduce: str = ProtoField(18, None)
    question: str = ProtoField(19, None)
    recent_notice: str = ProtoField(30, None)  # 30 chars


class GrpInfoOther(ProtoStruct):
    create_time: int = ProtoField(1)  # ?
    upgrade_time: int = ProtoField(4, None)  # when upgrade grp size?
    f5: int = ProtoField(5, None)  # unknown


class GrpInfo(ProtoStruct):
    grp_id: int = ProtoField(3)
    info: GrpInfoBasic = ProtoField(4)
    other: GrpInfoOther = ProtoField(5)


class GetGrpListResponse(ProtoStruct):
    grp_list: list[GrpInfo] = ProtoField(2, [])


class PBGetInfoFromUidReq(ProtoStruct):
    uid: list[str] = ProtoField(1)
    cfg: bytes = ProtoField(
        3,
        bytes.fromhex(
            "08a29c0108a39c0108a49c0108a59c0108a69c0108a79c0108a99c"
            "0108ab9c0108b49c0108b59c0108ba9c0108bf9c0108c59c011802"
        ),
    )


class GetInfoRspF1(ProtoStruct):
    type: int = ProtoField(1)
    value: int = ProtoField(2)


class GetInfoRspF2(ProtoStruct):
    type: int = ProtoField(1)
    value: bytes = ProtoField(2)

    @property
    def to_str(self) -> str:
        return self.value.decode()


class GetInfoRspField(ProtoStruct, debug=True):
    int_t: list[GetInfoRspF1] = ProtoField(1, [])
    str_t: list[GetInfoRspF2] = ProtoField(2, [])


class GetInfoRspBody(ProtoStruct):
    uid: str = ProtoField(1)
    fields: GetInfoRspField = ProtoField(2)


class GetInfoFromUidRsp(ProtoStruct):
    body: list[GetInfoRspBody] = ProtoField(1)
