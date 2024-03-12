from dataclasses import dataclass, field
from typing import List, Optional
from lagrange.client.message.elems import T


@dataclass
class MessageInfo:
    uid: str
    seq: int
    time: int
    rand: int


@dataclass
class GroupMessage(MessageInfo):
    uin: int
    grp_id: int
    grp_name: str
    nickname: str
    sub_id: int = field(repr=False)  # client ver identify
    msg: str
    msg_chain: List[T]


@dataclass
class GroupRecall(MessageInfo):
    grp_id: int
    suffix: str


@dataclass
class GroupMuteMember:
    """when target_uid is empty, mute all member"""
    operator_uid: str
    target_uid: str
    grp_id: int
    duration: int


@dataclass
class GroupMemberJoinRequest:
    grp_id: int
    uid: str
    _key: bytes  # unknown, field9
    src: int
    invitor_uid: Optional[str] = None
    answer: Optional[str] = None  # 问题：(.*)答案：(.*)


@dataclass
class GroupMemberJoined:
    uin: int
    uid: str
    join_type: int


@dataclass
class GroupMemberQuit:
    uin: int
    uid: str
    exit_type: int
    operator_uid: str = ""

    @property
    def is_kicked(self) -> bool:
        return self.exit_type == 131
