from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .heads import ContentHead, ResponseHead
from .msg import Message


class MsgPushBody(ProtoStruct):
    response_head: ResponseHead = proto_field(1)
    content_head: ContentHead = proto_field(2)
    message: Optional[Message] = proto_field(3, default=None)


class MsgPush(ProtoStruct):
    body: MsgPushBody = proto_field(1)
