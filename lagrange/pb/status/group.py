"""
Push Events
"""

from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class MemberChanged(ProtoStruct):
    uin: int = proto_field(1)
    uid: str = proto_field(3)
    exit_type: Optional[int] = proto_field(4, default=None)  # 3kick_me, 131kick, 130exit
    operator_uid: str = proto_field(5, default="")
    join_type: Optional[int] = proto_field(6, default=None)  # 6other, 0slef_invite
    join_type_new: Optional[int] = proto_field(
        4, default=None
    )  # 130 by_other(click url,scan qr,input grpid), 131 by_invite


class MemberJoinRequest(ProtoStruct):
    """JoinType: Direct(scan qrcode or search grp_id)"""

    grp_id: int = proto_field(1)
    uid: str = proto_field(3)
    src: int = proto_field(4)
    request_field: str = proto_field(5, default="")
    field_9: bytes = proto_field(9, default=b"")


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


class PBGroupReaction(ProtoStruct):
    inner: GroupReactionInner = proto_field(1)


class GroupSub16Head(ProtoStruct):
    timestamp: int = proto_field(2, default=0)
    uin: Optional[int] = proto_field(4, default=None)
    body: Optional[bytes] = proto_field(5, default=None)
    flag: Optional[int] = proto_field(
        13, default=None
    )  # 12: renamed, 6: set special_title, 13: unknown, 35: set reaction, 38: bot add
    operator_uid: str = proto_field(21, default="")
    f44: Optional[PBGroupReaction] = proto_field(44, default=None)  # set reaction only


class GroupSub20Head(ProtoStruct):
    f1: int = proto_field(1, default=None)  # 20
    grp_id: int = proto_field(4)
    f13: int = proto_field(13)  # 19
    body: "GroupSub20Body" = proto_field(26)


class GroupSub20Body(ProtoStruct):
    type: Optional[int] = proto_field(1, default=None)  # 12: nudge, 14: group_sign
    f2: int = proto_field(2)  # 1061 ,  bot added group:19217
    # f3: int = proto_field(3)  # 7
    # f6: int = proto_field(6)  # 1132
    attrs: list[dict] = proto_field(7, default_factory=list)
    attrs_xml: str = proto_field(8, default=None)
    f10: int = proto_field(10)  # rand?


class PBGroupAlbumUpdateBody(ProtoStruct):
    # f1: 6
    args: str = proto_field(2)


class PBGroupAlbumUpdate(ProtoStruct):
    # f1: 38
    timestamp: int = proto_field(2)
    grp_id: int = proto_field(4)
    # f13: 37
    body: PBGroupAlbumUpdateBody = proto_field(46)


# class InviteInner_what(ProtoStruct):
#     f1: int = proto_field(1)  # 0
#     f3: int = proto_field(3)  # 32
#     f4: bytes = proto_field(4)
#     f5: int = proto_field(5)
#     f6: str = proto_field(6)


# class InviteInfo_what(ProtoStruct):
#     inner: InviteInner_what = proto_field(1)


class PBGroupInvite(ProtoStruct):
    gid: int = proto_field(1)
    f2: int = proto_field(2)  # 1
    f3: int = proto_field(3)  # 4
    f4: int = proto_field(4)  # 0
    invitor_uid: str = proto_field(5)
    invite_info: bytes = proto_field(6)


class PBSelfJoinInGroup(ProtoStruct):
    gid: int = proto_field(1)
    f2: int = proto_field(2)
    f4: int = proto_field(4)  # 0
    f6: int = proto_field(6)  # 48
    f7: str = proto_field(7)
    operator_uid: str = proto_field(3)


class PBGroupBotAddedBody(ProtoStruct):
    grp_id: int = proto_field(1)
    bot_uid_1: Optional[str] = proto_field(2, default=None)
    bot_uid_2: Optional[str] = proto_field(3, default=None)  # f**k tx
    flag: int = proto_field(4)


class PBGroupBotAdded(ProtoStruct):
    # f1: 39
    grp_id: int = proto_field(4)
    # f13: 38
    body: PBGroupBotAddedBody = proto_field(47)


class PBGroupGrayTipBody(ProtoStruct):
    message: str = proto_field(2)
    flag: int = proto_field(3)


class PBBotGrayTip(ProtoStruct):
    # f1: 1
    grp_id: int = proto_field(4)
    body: PBGroupGrayTipBody = proto_field(5)
