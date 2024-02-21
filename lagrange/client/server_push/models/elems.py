from typing import TypeVar
from dataclasses import dataclass

from lagrange.info.serialize import JsonSerializer

T = TypeVar('T', "Text", "AtAll", "At", "Image", "Emoji")


@dataclass(slots=True)
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
    is_emoji: bool


@dataclass
class Emoji(BaseElem):
    id: int
