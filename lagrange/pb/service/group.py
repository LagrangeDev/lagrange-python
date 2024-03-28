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
