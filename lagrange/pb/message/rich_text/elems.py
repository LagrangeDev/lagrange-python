from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class ImageReserveArgs(ProtoStruct):
    is_emoji: bool = proto_field(1, default=False)
    display_name: str = proto_field(9, default="[图片]")


class Ptt(ProtoStruct):
    type: int = proto_field(1, default=4)
    to_uin: Optional[int] = proto_field(2, default=None)
    friend_file_key: Optional[str] = proto_field(3, default=None)
    md5: bytes = proto_field(4)
    name: str = proto_field(5)
    size: int = proto_field(6)
    reserved: Optional[bytes] = proto_field(7, default=None)
    file_id: Optional[int] = proto_field(8, default=None)  # available on grp msg
    is_valid: bool = proto_field(11, default=True)
    group_file_key: Optional[str] = proto_field(18, default=None)
    time: int = proto_field(19)
    format: int = proto_field(29, default=1)
    pb_reserved: dict = proto_field(30, default={1: 0})


class Text(ProtoStruct):
    string: str = proto_field(1, default="")
    # link: str = proto_field(2, default="")
    attr6_buf: Optional[bytes] = proto_field(3, default=None)
    # attr7_buf: bytes = proto_field(4, default=bytes())
    # buf: bytes = proto_field(11, default=bytes())
    pb_reserved: Optional[dict] = proto_field(12, default=None)


class Face(ProtoStruct):
    index: int = proto_field(1)


class OnlineImage(ProtoStruct):
    guid: bytes = proto_field(1)
    file_path: bytes = proto_field(2)


class NotOnlineImage(ProtoStruct):
    file_path: str = proto_field(1)
    file_len: int = proto_field(2)
    download_path: str = proto_field(3)
    image_type: int = proto_field(5)
    # image_preview: bytes = proto_field(6)
    file_md5: bytes = proto_field(7)
    height: int = proto_field(8)
    width: int = proto_field(9)
    res_id: str = proto_field(10)
    origin_path: Optional[str] = proto_field(15, default=None)
    args: ImageReserveArgs = proto_field(34, default=ImageReserveArgs())


class TransElem(ProtoStruct):
    elem_type: int = proto_field(1)
    elem_value: bytes = proto_field(2)


class MarketFace(ProtoStruct):
    name: str = proto_field(1, default="")
    item_type: int = proto_field(2)  # 6
    face_info: int = proto_field(3)  # 1
    face_id: bytes = proto_field(4)
    tab_id: int = proto_field(5)
    sub_type: int = proto_field(6)  # 3
    key: str = proto_field(7)  # hex, length=16
    # media_type: int = proto_field(9)
    width: int = proto_field(10)
    height: int = proto_field(11)
    pb_reserved: dict = proto_field(13)


class CustomFace(ProtoStruct):
    # guid: str = proto_field(1)
    file_path: str = proto_field(2)
    # shortcut: str = proto_field(3)
    fileid: int = proto_field(7)
    file_type: int = proto_field(10)
    md5: bytes = proto_field(13)
    thumb_url: Optional[str] = proto_field(14, default=None)
    big_url: Optional[str] = proto_field(15, default=None)
    original_url: str = proto_field(16)
    # biz_type: int = proto_field(17)
    image_type: int = proto_field(20, default=1000)
    width: int = proto_field(22)
    height: int = proto_field(23)
    size: int = proto_field(25)
    args: ImageReserveArgs = proto_field(34, default=ImageReserveArgs())


class ExtraInfo(ProtoStruct):
    nickname: str = proto_field(1, default="")
    group_card: str = proto_field(2, default="")
    level: int = proto_field(3)
    # sender_title: str = proto_field(7)
    # uin: int = proto_field(9)


class SrcMsgArgs(ProtoStruct):
    # new_id: int = proto_field(3, default=None)
    uid: Optional[str] = proto_field(6, default=None)


class SrcMsg(ProtoStruct):
    seq: int = proto_field(1)
    uin: int = proto_field(2, default=0)
    timestamp: int = proto_field(3)
    elems: list[dict] = proto_field(5, default=[{}])
    pb_reserved: Optional[SrcMsgArgs] = proto_field(8, default=None)
    to_uin: int = proto_field(10, default=0)


class MiniApp(ProtoStruct):
    template: bytes = proto_field(1)


class OpenData(ProtoStruct):
    data: bytes = proto_field(1)


class RichMsg(MiniApp):
    service_id: int = proto_field(2)


class CommonElem(ProtoStruct):
    service_type: int = proto_field(1)
    pb_elem: dict = proto_field(2)
    bus_type: int = proto_field(3)
