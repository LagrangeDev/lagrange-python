from dataclasses import dataclass
from typing import List


@dataclass
class MessageInfo:
    uin: int
    uid: str
    seq: int
    time: int
    rand: int


@dataclass
class GroupMessage(MessageInfo):
    grp_id: int
    grp_name: str
    msg: str
    msg_chain: List[dict]
