from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from . import BaseEvent

if TYPE_CHECKING:
    from lagrange.client.message.types import Element


@dataclass
class MessageInfo:
    uid: str
    seq: int
    time: int
    rand: int


@dataclass
class GroupEvent(BaseEvent):
    grp_id: int


@dataclass
class GroupMessage(GroupEvent, MessageInfo):
    uin: int
    grp_name: str
    nickname: str
    sub_id: int = field(repr=False)  # client ver identify
    sender_type: int = field(repr=False)
    msg: str
    msg_chain: list[Element]

    @property
    def is_bot(self) -> bool:
        return self.sender_type == 3091


@dataclass
class GroupRecall(GroupEvent, MessageInfo):
    suffix: str


@dataclass
class GroupNudge(GroupEvent):
    sender_uin: int
    target_uin: int
    action: str
    suffix: str
    attrs: dict[str, str | int] = field(repr=False)
    attrs_xml: str = field(repr=False)


@dataclass
class GroupSign(GroupEvent):
    """群打卡"""

    uin: int
    nickname: str
    timestamp: int
    attrs: dict[str, str | int] = field(repr=False)
    attrs_xml: str = field(repr=False)


@dataclass
class GroupMuteMember(GroupEvent):
    """when target_uid is empty, mute all member"""

    operator_uid: str
    target_uid: str
    duration: int


@dataclass
class GroupMemberJoinRequest(GroupEvent):
    uid: str
    invitor_uid: str | None = None
    answer: str | None = None  # 问题：(.*)答案：(.*)


@dataclass
class GroupMemberJoined(GroupEvent):
    uin: int
    uid: str
    join_type: int


@dataclass
class GroupMemberQuit(GroupEvent):
    uin: int
    uid: str
    exit_type: int
    operator_uid: str = ""

    @property
    def is_kicked(self) -> bool:
        return self.exit_type in [3, 131]

    @property
    def is_kicked_self(self) -> bool:
        return self.exit_type == 3


@dataclass
class GroupMemberGotSpecialTitle(GroupEvent):
    grp_id: int
    member_uin: int
    special_title: str
    _detail_url: str = ""


@dataclass
class GroupNameChanged(GroupEvent):
    name_new: str
    timestamp: int
    operator_uid: str


@dataclass
class GroupReaction(GroupEvent):
    uid: str
    seq: int
    emoji_id: int
    emoji_type: int
    emoji_count: int
    type: int
    total_operations: int

    @property
    def is_increase(self) -> bool:
        return self.type == 1

    @property
    def is_emoji(self) -> bool:
        return self.emoji_type == 2


@dataclass
class GroupAlbumUpdate(GroupEvent):
    """群相册更新（上传）"""

    timestamp: int
    image_id: str


@dataclass
class GroupInvite(GroupEvent):
    invitor_uid: str


@dataclass
class GroupInviteAccept(GroupEvent):
    invitor_uin: int
    uin: int