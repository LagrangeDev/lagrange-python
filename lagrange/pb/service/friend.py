from typing import Optional

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
        default=[
            GetFriendBody(type=1, f2=GetFriendNumbers(f1=[103, 102, 20002, 27394])),
            GetFriendBody(type=4, f2=GetFriendNumbers(f1=[100, 101, 102])),
        ],
    )
    f10002: list[int] = proto_field(10002, default=[13578, 13579, 13573, 13572, 13568])
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


def propertys(properties: list[FriendProperty]):
    return {prop.code: prop.value for prop in properties}
