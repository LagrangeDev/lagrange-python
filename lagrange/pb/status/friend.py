from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class FriendRecallInfo(ProtoStruct):
    from_uid: str = proto_field(1)
    to_uid: str = proto_field(2)
    seq: int = proto_field(3)
    new_id: int = proto_field(4)
    time: int = proto_field(5)
    random: int = proto_field(6)
    package_num: int = proto_field(7)
    package_index: int = proto_field(8)
    div_seq: int = proto_field(9)


class PBFriendRecall(ProtoStruct):
    info: FriendRecallInfo = proto_field(1)


class FriendRequestInfo(ProtoStruct):
    to_uid: str = proto_field(1)
    from_uid: str = proto_field(2)
    source_new: int = proto_field(5)
    verify: str = proto_field(10)  # 验证消息：我是...
    source: str = proto_field(11)


class FriendRequestResult(ProtoStruct):
    result_code: int = proto_field(1)  # 0 表示成功 / 已添加


class FriendRequestNotify(ProtoStruct):
    to_uid: str = proto_field(1)
    from_uid: str = proto_field(2)
    status: int = proto_field(3)
    timestamp: int = proto_field(4)
    source: str = proto_field(5)


class PBFriendRequest(ProtoStruct):
    info: Optional[FriendRequestInfo] = proto_field(1, default=None)
    notify: Optional[FriendRequestNotify] = proto_field(2, default=None)
    result: Optional[FriendRequestResult] = proto_field(3, default=None)
