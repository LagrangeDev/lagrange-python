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
    seq: int
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