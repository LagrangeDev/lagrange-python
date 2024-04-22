from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class ImageReserveArgs(ProtoStruct):
    is_emoji: bool = ProtoField(1, False)
    display_name: str = ProtoField(9, "[图片]")


class Ptt(ProtoStruct):
    type: int = ProtoField(1, 4)
    to_uin: int = ProtoField(2, None)
    friend_file_key: str = ProtoField(3, None)
    md5: bytes = ProtoField(4)
    name: str = ProtoField(5)
    size: int = ProtoField(6)
    reserved: bytes = ProtoField(7, None)
    file_id: int = ProtoField(8, None)  # available on grp msg
    is_valid: bool = ProtoField(11, True)
    group_file_key: str = ProtoField(18, None)
    time: int = ProtoField(19)
    format: int = ProtoField(29, 1)
    pb_reserved: dict = ProtoField(30, {1: 0})


class Text(ProtoStruct):
    string: str = ProtoField(1, "")
    # link: str = ProtoField(2, "")
    attr6_buf: bytes = ProtoField(3, None)
    # attr7_buf: bytes = ProtoField(4, bytes())
    # buf: bytes = ProtoField(11, bytes())
    pb_reserved: dict = ProtoField(12, None)


class Face(ProtoStruct):
    index: int = ProtoField(1)


class OnlineImage(ProtoStruct):
    guid: bytes = ProtoField(1)
    file_path: bytes = ProtoField(2)


class NotOnlineImage(ProtoStruct):
    file_path: str = ProtoField(1)
    file_len: int = ProtoField(2)
    download_path: str = ProtoField(3)
    image_type: int = ProtoField(5)
    # image_preview: bytes = ProtoField(6)
    file_md5: bytes = ProtoField(7)
    height: int = ProtoField(8)
    width: int = ProtoField(9)
    res_id: str = ProtoField(10)
    origin_path: str = ProtoField(15, None)
    args: ImageReserveArgs = ProtoField(34, ImageReserveArgs())


class TransElem(ProtoStruct):
    elem_type: int = ProtoField(1)
    elem_value: bytes = ProtoField(2)


class MarketFace(ProtoStruct):
    name: str = ProtoField(1, "")
    item_type: int = ProtoField(2)  # 6
    face_info: int = ProtoField(3)  # 1
    face_id: bytes = ProtoField(4)
    tab_id: int = ProtoField(5)
    sub_type: int = ProtoField(6)  # 3
    key: str = ProtoField(7)  # hex, length=16
    # media_type: int = ProtoField(9)
    width: int = ProtoField(10)
    height: int = ProtoField(11)
    pb_reserved: dict = ProtoField(13)


class CustomFace(ProtoStruct):
    # guid: str = ProtoField(1)
    file_path: str = ProtoField(2)
    # shortcut: str = ProtoField(3)
    fileid: int = ProtoField(7)
    file_type: int = ProtoField(10)
    md5: bytes = ProtoField(13)
    thumb_url: str = ProtoField(14, None)
    big_url: str = ProtoField(15, None)
    original_url: str = ProtoField(16)
    # biz_type: int = ProtoField(17)
    image_type: int = ProtoField(20, 1000)
    width: int = ProtoField(22)
    height: int = ProtoField(23)
    size: int = ProtoField(25)
    args: ImageReserveArgs = ProtoField(34, ImageReserveArgs())


class ExtraInfo(ProtoStruct):
    nickname: str = ProtoField(1, "")
    group_card: str = ProtoField(2, "")
    level: int = ProtoField(3)
    # sender_title: str = ProtoField(7)
    # uin: int = ProtoField(9)


class SrcMsgArgs(ProtoStruct):
    # new_id: int = ProtoField(3, None)
    uid: str = ProtoField(6, None)


class SrcMsg(ProtoStruct):
    seq: int = ProtoField(1)
    uin: int = ProtoField(2, 0)
    timestamp: int = ProtoField(3)
    elems: list[dict] = ProtoField(5, [{}])
    pb_reserved: SrcMsgArgs = ProtoField(8, None)
    to_uin: int = ProtoField(10, 0)


class MiniApp(ProtoStruct):
    template: bytes = ProtoField(1)


class OpenData(ProtoStruct):
    data: bytes = ProtoField(1)


class RichMsg(MiniApp):
    service_id: int = ProtoField(2)


class CommonElem(ProtoStruct):
    service_type: int = ProtoField(1)
    pb_elem: dict = ProtoField(2)
    bus_type: int = ProtoField(3)
