from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from . import BaseEvent

if TYPE_CHECKING:
    from lagrange.client.message.types import Element


@dataclass
class FriendEvent(BaseEvent):
    from_uin: int
    from_uid: str
    to_uin: int
    to_uid: str


@dataclass
class FriendMessage(FriendEvent):
    seq: int  # c2cMsgSeq (content_head f11)
    client_seq: int  # 发送方 clientSequence (content_head f5)
    msg_id: int
    timestamp: int
    msg: str
    msg_chain: list[Element]


@dataclass
class FriendRecall(FriendEvent):
    seq: int
    msg_id: int
    timestamp: int


@dataclass
class FriendRequest(FriendEvent):
    from_uid: str
    to_uid: str
    message: str
    source: str


@dataclass
class FriendRequestFinished(FriendEvent):
    result: int  # 0 表示成功 / 已添加


@dataclass
class FriendAddNotify(FriendEvent):
    status: int
    timestamp: int
    source: str
