from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField
from .heads import ContentHead, ResponseHead
from .msg import Message


class MsgPushBody(ProtoStruct):
    response_head: ResponseHead = ProtoField(1)
    content_head: ContentHead = ProtoField(2)
    message: Message = ProtoField(3, None)


class MsgPush(ProtoStruct):
    body: MsgPushBody = ProtoField(1)
