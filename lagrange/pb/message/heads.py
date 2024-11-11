from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class ContentHead(ProtoStruct):
    type: int = proto_field(1)
    sub_type: Optional[int] = proto_field(2, default=None)  # when send ,private is 175, group is None
    f3: Optional[int] = proto_field(3, default=None)  # In forward msg, this field like sub_type
    random: int = proto_field(4, default=0)
    seq: int = proto_field(5, default=0)
    timestamp: int = proto_field(6, default=0)
    pkg_num: int = proto_field(7, default=1)
    pkg_index: int = proto_field(8, default=0)
    div_seq: int = proto_field(9, default=0)
    c2c_seq: Optional[int] = proto_field(11, default=None)
    # new_id: int = proto_field(12)
    forward: Optional["Forward"] = proto_field(15, default=None)


class Grp(ProtoStruct):
    gid: int = proto_field(1, default=0)
    sender_name: str = proto_field(4, default="")  # empty in get_grp_msg
    grp_name: str = proto_field(7, default="")


class ResponseHead(ProtoStruct):
    from_uin: int = proto_field(1, default=0)
    from_uid: str = proto_field(2, default="")
    type: int = proto_field(3, default=0)
    sigmap: int = proto_field(4, default=0)
    to_uin: int = proto_field(5, default=0)
    to_uid: str = proto_field(6, default="")
    rsp_grp: Optional[Grp] = proto_field(8, default=None)


class Forward(ProtoStruct):
    f1: int = proto_field(1, default=0)
    f2: int = proto_field(2, default=0)
    f3: int = proto_field(3, default=0)
    f4: bytes = proto_field(4, default=b"")
    f5: bytes = proto_field(5, default=b"")
