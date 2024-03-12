from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField
from .elems import (
    Ptt,
    Text,
    Face,
    OnlineImage,
    NotOnlineImage,
    TransElem,
    MarketFace,
    CustomFace,
    RichMsg,
    ExtraInfo,
    SrcMsg,
    MiniApp,
    OpenData,
)


__all__ = ["Elems", "RichText"]


class Elems(ProtoStruct):
    text: Text = ProtoField(1, None)
    face: Face = ProtoField(2, None)
    online_image: OnlineImage = ProtoField(3, None)
    not_online_image: NotOnlineImage = ProtoField(4, None)
    trans_elem: TransElem = ProtoField(5, None)
    market_face: MarketFace = ProtoField(6, None)
    custom_face: CustomFace = ProtoField(8, None)
    #elem_flags2: ElemFlags2 = ProtoField(9, None)
    rich_msg: RichMsg = ProtoField(12, None)
    extra_info: ExtraInfo = ProtoField(16, None)
    #video_file: VideoFile = ProtoField(19, None)
    open_data: OpenData = ProtoField(41, None)
    src_msg: SrcMsg = ProtoField(45, None)
    mini_app: MiniApp = ProtoField(51, None)


class RichText(ProtoStruct):
    attrs: dict = ProtoField(1, {})
    content: list[Elems] = ProtoField(2)
    not_online_file: dict = ProtoField(3, {})
    ptt: Ptt = ProtoField(4, None)
