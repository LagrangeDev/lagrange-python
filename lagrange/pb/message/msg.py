from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField
from .rich_text import RichText


class Message(ProtoStruct):
    body: RichText = ProtoField(1, None)
    buf2: bytes = ProtoField(2, bytes())
    buf3: bytes = ProtoField(3, bytes())
