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


class GroupReactionMsg(ProtoStruct):
    id: int = proto_field(1)
    total_operations: int = proto_field(2)
    # f3: int = proto_field(3)  # 4


class GroupReactionDetail(ProtoStruct):
    emo_id: str = proto_field(1)  # string type Unicode
    emo_type: int = proto_field(2)  # 1: qq internal emoji, 2: unicode emoji
    count: int = proto_field(3, default=0)
    send_type: int = proto_field(5)  # 1: set, 2: remove
    sender_uid: str = proto_field(4)


class GroupReactionBody(ProtoStruct):
    op_id: int = proto_field(1)
    msg: GroupReactionMsg = proto_field(2)
    detail: GroupReactionDetail = proto_field(3)


class GroupReactionInner(ProtoStruct):
    body: GroupReactionBody = proto_field(1)


class GroupReaction(ProtoStruct):
    inner: GroupReactionInner = proto_field(1)


class GroupSub16Head(ProtoStruct):
    timestamp: int = proto_field(2, default=0)
    uin: Optional[int] = proto_field(4, default=None)
    body: Optional[bytes] = proto_field(5, default=None)
    flag: int = proto_field(
        13
    )  # 12: renamed, 6: set special_title, 13: unknown, 35: set reaction
    operator_uid: str = proto_field(21, default="")
    f44: Optional[GroupReaction] = proto_field(44, default=None)  # set reaction only


class GroupSub20Body(ProtoStruct):
    type: int = proto_field(1)  # 12: nudge, 14: group_sign
    # f2: int = proto_field(2)  # 1061
    # f3: int = proto_field(3)  # 7
    # f6: int = proto_field(6)  # 1132
    attrs: list[dict] = proto_field(7, default={})
    attrs_xml: str = proto_field(8, default=None)
    f10: int = proto_field(10)  # rand?


class GroupSub20Head(ProtoStruct):
    f1: int = proto_field(1)  # 20
    grp_id: int = proto_field(4)
    f13: int = proto_field(13)  # 19
    body: GroupSub20Body = proto_field(26)
