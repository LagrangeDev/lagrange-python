from dataclasses import dataclass
from typing import List

from . import BaseEvent


@dataclass
class ClientOffline(BaseEvent):
    recoverable: bool


@dataclass
class ClientOnline(BaseEvent):
    """after register completed"""


@dataclass
class ServerKick(BaseEvent):
    tips: str
    title: str


@dataclass
class OtherClientInfo(BaseEvent):
    @dataclass
    class ClientOnline(BaseEvent):
        sub_id: int
        os_name: str
        device_name: str

    clients: List[ClientOnline]
