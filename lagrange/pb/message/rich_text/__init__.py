from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct

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
    text: Text = ProtoField(1, None)
    face: Face = ProtoField(2, None)
    online_image: OnlineImage = ProtoField(3, None)
    not_online_image: NotOnlineImage = ProtoField(4, None)
    trans_elem: TransElem = ProtoField(5, None)
    market_face: MarketFace = ProtoField(6, None)
    custom_face: CustomFace = ProtoField(8, None)
    elem_flags2: bytes = ProtoField(9, None)
    rich_msg: RichMsg = ProtoField(12, None)
    extra_info: ExtraInfo = ProtoField(16, None)
    # video_file: VideoFile = ProtoField(19, None)
    general_flags: bytes = ProtoField(37, None)
    open_data: OpenData = ProtoField(41, None)
    src_msg: SrcMsg = ProtoField(45, None)
    mini_app: MiniApp = ProtoField(51, None)
    common_elem: CommonElem = ProtoField(53, None)


class RichText(ProtoStruct):
    attrs: dict = ProtoField(1, None)
    content: list[Elems] = ProtoField(2)
    not_online_file: dict = ProtoField(3, None)
    ptt: Ptt = ProtoField(4, None)
