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
class CompatibleText(BaseElem):
    """仅用于兼容性变更，不应作为判断条件"""

    @property
    def text(self) -> str:
        return self.display

    @text.setter
    def text(self, text: str):
        """ignore"""


@dataclass
class MediaInfo:
    name: str
    size: int
    url: str
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
class Quote(CompatibleText):
    seq: int
    uin: int
    timestamp: int
    uid: str = ""
    msg: str = ""

    @classmethod
    def build(cls, ev: GroupMessage) -> "Quote":
        return cls(
            seq=ev.seq,
            uid=ev.uid,
            uin=ev.uin,
            timestamp=ev.time,
            msg=ev.msg,
        )

    @property
    def display(self) -> str:
        return f"[quote:{self.msg}]"


@dataclass
class Json(CompatibleText):
    raw: bytes

    def to_dict(self) -> dict:
        return json.loads(self.raw)

    @property
    def display(self) -> str:
        return f"[json:{len(self.raw)}]"


@dataclass
class Service(Json):
    id: int

    @property
    def display(self) -> str:
        return f"[service:{self.id}]"


@dataclass
class AtAll(BaseElem):
    text: str

    @property
    def display(self) -> str:
        return self.text


@dataclass
class At(BaseElem):
    text: str
    uin: int
    uid: str

    @classmethod
    def build(cls, ev: GroupMessage) -> "At":
        return cls(uin=ev.uin, uid=ev.uid, text=f"@{ev.nickname or ev.uin}")


@dataclass
class Image(CompatibleText, MediaInfo):
    width: int
    height: int
    is_emoji: bool
    display_name: str

    @property
    def display(self) -> str:
        return self.display_name


@dataclass
class Video(CompatibleText, MediaInfo):
    width: int
    height: int
    time: int
    file_key: str = field(repr=True)

    @property
    def display(self) -> str:
        return f"[video:{self.width}x{self.height},{self.time}s]"


@dataclass
class Audio(CompatibleText, MediaInfo):
    time: int
    file_key: str = field(repr=True)

    @property
    def display(self) -> str:
        return f"[audio:{self.time}]"


@dataclass
class Raw(CompatibleText):
    data: bytes

    @property
    def display(self) -> str:
        return f"[raw:{len(self.data)}]"


@dataclass
class Emoji(CompatibleText):
    id: int

    @property
    def display(self) -> str:
        return f"[emoji:{self.id}]"


@dataclass
class Reaction(Emoji):
    """QQ: super emoji"""

    # text: str
    # show_type: int  # size - sm: 33, bg: 37


@dataclass
class Poke(CompatibleText):
    id: int
    f7: int = 0
    f8: int = 0

    @property
    def display(self) -> str:
        return f"[poke:{self.id}]"


@dataclass
class MarketFace(CompatibleText):
    name: str
    face_id: bytes
    tab_id: int
    width: int
    height: int

    @property
    def url(self) -> str:
        pic_id = self.face_id.hex()
        return f"https://i.gtimg.cn/club/item/parcel/item/{pic_id[:2]}/{pic_id}/{self.width}x{self.height}.png"

    @property
    def display(self) -> str:
        return f"[marketface:{self.name}]"


@dataclass
class File(CompatibleText):
    file_size: int
    file_name: str
    file_md5: bytes
    file_url: Optional[str]
    file_id: Optional[str]  # only in group
    file_uuid: Optional[str]  # only in private
    file_hash: Optional[str]

    @property
    def display(self) -> str:
        return f"[file:{self.file_name}]"

    @classmethod
    def _paste_build(
        cls,
        file_size: int,
        file_name: str,
        file_md5: bytes,
        file_id: Optional[str] = None,
        file_uuid: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> "File":
        return cls(
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


@dataclass
class GreyTips(BaseElem):
    """
    奇怪的整活元素
    建议搭配Text使用
    冷却3分钟左右？
    """

    text: str

    @property
    def display(self) -> str:
        return f"<GreyTips: {self.text}>"


@dataclass
class Markdown(BaseElem):
    content: str

    @property
    def display(self) -> str:
        return f"[markdown:{self.md_c.decode()}]"


class Permission:
    type: int
    specify_role_ids: Optional[list[str]]
    specify_user_ids: Optional[list[str]]


class RenderData:
    label: Optional[str]
    visited_label: Optional[str]
    style: int


class Action:
    type: Optional[int]
    permission: Optional[Permission]
    data: str
    reply: bool
    enter: bool
    anchor: Optional[int]
    unsupport_tips: Optional[str]
    click_limit: Optional[int]  # deprecated
    at_bot_show_channel_list: bool  # deprecated


class Button:
    id: Optional[str]
    render_data: Optional[RenderData]
    action: Optional[Action]


class InlineKeyboardRow:
    buttons: Optional[list[Button]]


class InlineKeyboard:
    rows: list[InlineKeyboardRow]


@dataclass
class Keyboard(Text):
    content: Optional[list[InlineKeyboard]]
    bot_appid: int

    @property
    def display(self) -> str:
        return f"[keyboard:{self.bot_appid}]"
