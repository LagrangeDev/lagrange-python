"""
Push Events
"""

from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


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
