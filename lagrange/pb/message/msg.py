from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .rich_text import RichText


class Message(ProtoStruct):
    body: Optional[RichText] = proto_field(1, default=None)
    buf2: Optional[bytes] = proto_field(2, default=None)
    buf3: Optional[bytes] = proto_field(3, default=None)
