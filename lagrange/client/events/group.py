from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from lagrange.client.message.types import T


@dataclass
class MessageInfo:
    uid: str
    seq: int
    time: int
    rand: int


@dataclass
class GroupEvent:
    grp_id: int


@dataclass
class GroupMessage(GroupEvent, MessageInfo):
    uin: int
    grp_name: str
    nickname: str
    sub_id: int = field(repr=False)  # client ver identify
    msg: str
    msg_chain: List[T]


@dataclass
class GroupRecall(GroupEvent, MessageInfo):
    suffix: str


@dataclass
class GroupMuteMember(GroupEvent):
    """when target_uid is empty, mute all member"""

    operator_uid: str
    target_uid: str
    duration: int


@dataclass
class GroupMemberJoinRequest(GroupEvent):
    uid: str
    invitor_uid: Optional[str] = None
    answer: Optional[str] = None  # 问题：(.*)答案：(.*)


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
        return self.exit_type == 131


@dataclass
class GroupMemberGotSpecialTitle(GroupEvent):
    grp_id: int
    member_uin: int
    special_title: str
    _detail_url: str = ""


@dataclass
class GroupNameChanged:
    grp_id: int
    name_new: str
    timestamp: int
    operator_uid: str
