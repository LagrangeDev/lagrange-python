"""
Push Events
"""

from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class MemberChanged(ProtoStruct):
    uin: int = ProtoField(1)
    uid: str = ProtoField(3)
    exit_type: int = ProtoField(4, None)  # 131kick, 130exit
    operator_uid: str = ProtoField(5, "")
    join_type: int = ProtoField(6, None)  # 6scanqr,


class MemberJoinRequest(ProtoStruct):
    """JoinType: Direct(scan qrcode or search grp_id)"""

    grp_id: int = ProtoField(1)
    uid: str = ProtoField(3)
    src: int = ProtoField(4)
    request_field: str = ProtoField(5, "")
    field_9: bytes = ProtoField(9, bytes())


class InviteInner(ProtoStruct):
    grp_id: int = ProtoField(1)
    uid: str = ProtoField(5)
    invitor_uid: str = ProtoField(6)


class InviteInfo(ProtoStruct):
    inner: InviteInner = ProtoField(1)


class MemberInviteRequest(ProtoStruct):
    """JoinType: From Friends(share link or others)"""

    cmd: int = ProtoField(1)
    info: InviteInfo = ProtoField(2)


class MemberGotTitleBody(ProtoStruct):
    string: str = ProtoField(2)
    f3: int = ProtoField(3)
    member_uin: int = ProtoField(5)


class RecallMsgInfo(ProtoStruct):
    seq: int = ProtoField(1)
    time: int = ProtoField(2)
    rand: int = ProtoField(3)
    uid: str = ProtoField(6)


class RecallMsgExtra(ProtoStruct):
    suffix: str = ProtoField(2, "")


class MemberRecallMsgBody(ProtoStruct):
    uid: str = ProtoField(1)
    info: RecallMsgInfo = ProtoField(3)
    extra: RecallMsgExtra = ProtoField(9, None)


class MemberRecallMsg(ProtoStruct):
    body: MemberRecallMsgBody = ProtoField(11)


class GroupRenamedBody(ProtoStruct):
    type: int = ProtoField(1)  # unknown
    grp_name: str = ProtoField(2)


class GroupSub16Head(ProtoStruct):
    timestamp: int = ProtoField(2, 0)
    uin: int = ProtoField(4, None)
    body: bytes = ProtoField(5, None)
    flag: int = ProtoField(13)  # 12: renamed, 6: set special_title, 13: unknown
    operator_uid: str = ProtoField(21, "")
