from dataclasses import dataclass

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
