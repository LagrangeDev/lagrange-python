import json
from dataclasses import dataclass, field
from typing import Optional

from lagrange.client.events.group import GroupMessage
from lagrange.info.serialize import JsonSerializer


@dataclass
class BaseElem(JsonSerializer):
    @property
    def display(self) -> str:
        return ""

    @property
    def type(self) -> str:
        return self.__class__.__name__.lower()


@dataclass
class MediaInfo:
    name: str
    size: int
    id: int = field(repr=False)
    md5: bytes = field(repr=False)
    qmsg: Optional[bytes] = field(repr=False)  # not online image


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
    timestamp: int
    uid: str = ""
    msg: str = ""

    @classmethod
    def build(cls, ev: GroupMessage) -> "Quote":
        return cls(
            text=f"[quote:{ev.msg}]",
            seq=ev.seq,
            uid=ev.uid,
            uin=ev.uin,
            timestamp=ev.time,
            msg=ev.msg,
        )


@dataclass
class Json(Text):
    raw: bytes

    def to_dict(self) -> dict:
        return json.loads(self.raw)


@dataclass
class Service(Json):
    id: int


@dataclass
class AtAll(Text): ...


@dataclass
class At(Text):
    uin: int
    uid: str

    @classmethod
    def build(cls, ev: GroupMessage) -> "At":
        return cls(uin=ev.uin, uid=ev.uid, text=f"@{ev.nickname or ev.uin}")


@dataclass
class Image(Text, MediaInfo):
    width: int
    height: int
    url: str
    is_emoji: bool


@dataclass
class Video(Text, MediaInfo):
    width: int
    height: int
    time: int
    file_key: str = field(repr=True)


@dataclass
class Audio(Text, MediaInfo):
    time: int
    file_key: str = field(repr=True)


@dataclass
class Raw(Text):
    data: bytes


@dataclass
class Emoji(BaseElem):
    id: int

    @property
    def text(self) -> str:
        return f"[emoji:{self.id}]"


@dataclass
class Reaction(Emoji):
    """QQ: super emoji"""

    # text: str
    # show_type: int  # size - sm: 33, bg: 37


@dataclass
class Poke(Text):
    id: int
    f7: int = 0
    f8: int = 0


@dataclass
class MarketFace(Text):
    face_id: bytes
    tab_id: int
    width: int
    height: int

    @property
    def url(self) -> str:
        pic_id = self.face_id.hex()
        return f"https://i.gtimg.cn/club/item/parcel/item/{pic_id[:2]}/{pic_id}/{self.width}x{self.height}.png"


@dataclass
class File(Text):
    file_size: int
    file_name: str
    file_md5: bytes
    file_url: Optional[str]
    file_id: Optional[str]  # only in group
    file_uuid: Optional[str]  # only in private
    file_hash: Optional[str]

    @classmethod
    def _paste_build(cls, file_size: int, file_name: str,
                     file_md5: bytes, file_id: Optional[str] = None,
                     file_uuid: Optional[str] = None, file_hash: Optional[str] = None) -> "File":
        return cls(
            text=f"[file:{file_name}]",
            file_size=file_size,
            file_name=file_name,
            file_md5=file_md5,
            file_url=None,
            file_id=file_id,
            file_uuid=file_uuid,
            file_hash=file_hash,
        )

    @classmethod
    def grp_paste_build(cls, file_size: int, file_name: str, file_md5: bytes, file_id: str) -> "File":
        return cls._paste_build(file_size, file_name, file_md5, file_id=file_id)

    @classmethod
    def pri_paste_build(cls, file_size: int, file_name: str, file_md5: bytes, file_uuid: str, file_hash: str) -> "File":
        return cls._paste_build(file_size, file_name, file_md5, file_uuid=file_uuid, file_hash=file_hash)
