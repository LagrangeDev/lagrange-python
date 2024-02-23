import json
from typing import TypeVar
from dataclasses import dataclass, field

from lagrange.info.serialize import JsonSerializer

T = TypeVar('T', "Text", "AtAll", "At", "Image", "Emoji", "Json")


@dataclass
class BaseElem(JsonSerializer):
    @property
    def display(self) -> str:
        return ""

    @property
    def type(self) -> str:
        return self.__class__.__name__.lower()


@dataclass
class Text(BaseElem):
    text: str

    @property
    def display(self) -> str:
        return self.text


@dataclass
class Quote(Text):
    seq: int
    uin: int
    uid: str
    timestamp: int


@dataclass
class Json(Text):
    raw: bytes

    def to_dict(self) -> dict:
        return json.loads(self.raw)


@dataclass
class Service(Json):
    id: int


@dataclass
class AtAll(Text):
    ...


@dataclass
class At(Text):
    uin: int
    uid: str


@dataclass
class Image(Text):
    url: str
    name: str
    width: int
    height: int
    size: int
    id: int = field(repr=False)
    md5: bytes = field(repr=False)
    is_emoji: bool


@dataclass
class Emoji(BaseElem):
    id: int


@dataclass
class Reaction(Emoji):
    """QQ: super emoji"""
    text: str
    show_type: int  # size - sm: 33, bg: 37