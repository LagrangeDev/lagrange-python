from typing import Optional

from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.utils.binary.protobuf import ProtoStruct, proto_field


class FriendProperty(ProtoStruct):
    code: int = proto_field(1)
    value: Optional[str] = proto_field(2, default=None)


class FriendLayer1(ProtoStruct):
    properties: list[FriendProperty] = proto_field(2, default=None)


class FriendAdditional(ProtoStruct):
    type: int = proto_field(1)
    layer1: FriendLayer1 = proto_field(2)


class FriendInfo(ProtoStruct):
    uid: str = proto_field(1)
    custom_group: Optional[int] = proto_field(2, default=None)
    uin: int = proto_field(3)
    additional: list[FriendAdditional] = proto_field(10001)


class GetFriendNumbers(ProtoStruct):
    f1: list[int] = proto_field(1)


class GetFriendBody(ProtoStruct):
    type: int = proto_field(1)
    f2: GetFriendNumbers = proto_field(2)


class GetFriendListUin(ProtoStruct):
    uin: int = proto_field(1)


class PBGetFriendListRequest(ProtoStruct):
    friend_count: int = proto_field(2, default=300)  # paging get num
    f4: int = proto_field(4, default=0)
    next_uin: Optional[GetFriendListUin] = proto_field(5, default=None)
    f6: int = proto_field(6, default=1)
    f7: int = proto_field(7, default=2147483647)  # MaxValue
    body: list[GetFriendBody] = proto_field(
        10001,
        default_factory=lambda: [
            GetFriendBody(type=1, f2=GetFriendNumbers(f1=[103, 102, 20002, 27394])),
            GetFriendBody(type=4, f2=GetFriendNumbers(f1=[100, 101, 102])),
        ],
    )
    f10002: list[int] = proto_field(10002, default_factory=lambda: [13578, 13579, 13573, 13572, 13568])
    f10003: int = proto_field(10003, default=4051)
    """
    * GetFriendNumbers里是要拿到的东西
    * 102：个性签名
    * 103：备注
    * 20002：昵称
    * 27394：QID
    """


class GetFriendListRsp(ProtoStruct):
    next: Optional[GetFriendListUin] = proto_field(2, default=None)
    display_friend_count: int = proto_field(3)
    timestamp: int = proto_field(6)
    self_uin: int = proto_field(7)
    friend_list: list[FriendInfo] = proto_field(101)


class FriendLikeReq(ProtoStruct):
    uid: str = proto_field(11)
    field12: int = proto_field(12)  # 71
    count: int = proto_field(13)


class FriendLikeRsp(ProtoStruct):
    added: int = proto_field(13)
    total: int = proto_field(14)


class PBHandleFriendRequest(ProtoStruct):
    action: int = proto_field(1)
    target_uid: str = proto_field(2)


class FriendRecallMsgInfo(ProtoStruct):
    client_seq: int = proto_field(1)
    rand: int = proto_field(2)
    msg_id: int = proto_field(3)
    time: int = proto_field(4)
    field5: int = proto_field(5, default=0)
    c2c_seq: int = proto_field(6)


class FriendRecallMsgSettings(ProtoStruct):
    field1: bool = proto_field(1, default=False)
    field2: bool = proto_field(2, default=False)


class RecallFriendMsgRequest(ProtoStruct):
    typs: int = proto_field(1, default=1)
    uid: str = proto_field(3)
    info: FriendRecallMsgInfo = proto_field(4)
    settings: FriendRecallMsgSettings = proto_field(5, default_factory=FriendRecallMsgSettings)
    field6: bool = proto_field(6, default=False)

    @classmethod
    def build(cls, uid: str, client_seq: int, c2c_seq: int, rand: int, timestamp: int) -> "RecallFriendMsgRequest":
        return cls(
            uid=uid,
            info=FriendRecallMsgInfo(
                client_seq=client_seq, rand=rand, msg_id=(0x01000000 << 32) | rand, time=timestamp, c2c_seq=c2c_seq
            ),
        )


class GetFriendMsgRequest(ProtoStruct):
    uid: Optional[str] = proto_field(2)
    start: int = proto_field(3)
    end: int = proto_field(4)


class GetFriendMsgRsp(ProtoStruct):
    ret_code: Optional[int] = proto_field(1, default=None)
    msg: Optional[str] = proto_field(2, default=None)
    uid: Optional[str] = proto_field(4, default=None)
    messages: list[MsgPushBody] = proto_field(7, default_factory=list)


class GetFriendPeerSeqReq(ProtoStruct):
    uid: str = proto_field(1)


class GetFriendPeerSeqRsp(ProtoStruct):
    seq1: int = proto_field(3, default=0)
    seq2: int = proto_field(4, default=0)
    latest_msg_time: int = proto_field(5, default=0)


class RecallFriendMsgEcho(ProtoStruct):
    info: FriendRecallMsgInfo = proto_field(3)


class RecallFriendMsgRsp(ProtoStruct):
    ret_code: Optional[int] = proto_field(1, default=None)
    err_msg: Optional[str] = proto_field(2, default=None)
    field3: int = proto_field(3, default=0)
    echo: Optional[RecallFriendMsgEcho] = proto_field(5, default=None)
    field6: bytes = proto_field(6, default=b"")


def propertys(properties: list[FriendProperty]):
    return {prop.code: prop.value for prop in properties}
