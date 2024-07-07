"""
Push Events
"""
from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class MemberChanged(ProtoStruct):
    uin: int = proto_field(1)
    uid: str = proto_field(3)
    exit_type: Optional[int] = proto_field(4, default=None)  # 131kick, 130exit
    operator_uid: str = proto_field(5, default="")
    join_type: Optional[int] = proto_field(6, default=None)  # 6scanqr,


class MemberJoinRequest(ProtoStruct):
    """JoinType: Direct(scan qrcode or search grp_id)"""

    grp_id: int = proto_field(1)
    uid: str = proto_field(3)
    src: int = proto_field(4)
    request_field: str = proto_field(5, default="")
    field_9: bytes = proto_field(9, default=bytes())


class InviteInner(ProtoStruct):
    grp_id: int = proto_field(1)
    uid: str = proto_field(5)
    invitor_uid: str = proto_field(6)


class InviteInfo(ProtoStruct):
    inner: InviteInner = proto_field(1)


class MemberInviteRequest(ProtoStruct):
    """JoinType: From Friends(share link or others)"""

    cmd: int = proto_field(1)
    info: InviteInfo = proto_field(2)


class MemberGotTitleBody(ProtoStruct):
    string: str = proto_field(2)
    f3: int = proto_field(3)
    member_uin: int = proto_field(5)


class RecallMsgInfo(ProtoStruct):
    seq: int = proto_field(1)
    time: int = proto_field(2)
    rand: int = proto_field(3)
    uid: str = proto_field(6)


class RecallMsgExtra(ProtoStruct):
    suffix: str = proto_field(2, default="")


class MemberRecallMsgBody(ProtoStruct):
    uid: str = proto_field(1)
    info: RecallMsgInfo = proto_field(3)
    extra: Optional[RecallMsgExtra] = proto_field(9, default=None)


class MemberRecallMsg(ProtoStruct):
    body: MemberRecallMsgBody = proto_field(11)


class GroupRenamedBody(ProtoStruct):
    type: int = proto_field(1)  # unknown
    grp_name: str = proto_field(2)


class GroupSub16Head(ProtoStruct):
    timestamp: int = proto_field(2, default=0)
    uin: Optional[int] = proto_field(4, default=None)
    body: Optional[bytes] = proto_field(5, default=None)
    flag: int = proto_field(13)  # 12: renamed, 6: set special_title, 13: unknown
    operator_uid: str = proto_field(21, default="")
