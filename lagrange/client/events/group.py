from dataclasses import dataclass, field
from typing import List
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
