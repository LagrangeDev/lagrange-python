from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .elems import (
    CommonElem,
    CustomFace,
    ExtraInfo,
    Face,
    MarketFace,
    MiniApp,
    NotOnlineImage,
    OnlineImage,
    OpenData,
    Ptt,
    RichMsg,
    SrcMsg,
    Text,
    TransElem,
)

__all__ = ["Elems", "RichText"]


class Elems(ProtoStruct, debug=True):
    text: Optional[Text] = proto_field(1, default=None)
    face: Optional[Face] = proto_field(2, default=None)
    online_image: Optional[OnlineImage] = proto_field(3, default=None)
    not_online_image: Optional[NotOnlineImage] = proto_field(4, default=None)
    trans_elem: Optional[TransElem] = proto_field(5, default=None)
    market_face: Optional[MarketFace] = proto_field(6, default=None)
    custom_face: Optional[CustomFace] = proto_field(8, default=None)
    elem_flags2: Optional[bytes] = proto_field(9, default=None)
    rich_msg: Optional[RichMsg] = proto_field(12, default=None)
    extra_info: Optional[ExtraInfo] = proto_field(16, default=None)
    # video_file: VideoFile = proto_field(19, default=None)
    general_flags: Optional[bytes] = proto_field(37, default=None)
    open_data: Optional[OpenData] = proto_field(41, default=None)
    src_msg: Optional[SrcMsg] = proto_field(45, default=None)
    mini_app: Optional[MiniApp] = proto_field(51, default=None)
    common_elem: Optional[CommonElem] = proto_field(53, default=None)


class RichText(ProtoStruct):
    attrs: Optional[dict] = proto_field(1, default=None)
    content: list[Elems] = proto_field(2)
    not_online_file: Optional[dict] = proto_field(3, default=None)
    ptt: Optional[Ptt] = proto_field(4, default=None)
