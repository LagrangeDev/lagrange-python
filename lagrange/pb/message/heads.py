from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class ContentHead(ProtoStruct):
    type: int = proto_field(1)
    sub_type: int = proto_field(2, default=0)
    msg_id: int = proto_field(4, default=0)
    seq: int = proto_field(5, default=0)
    timestamp: int = proto_field(6, default=0)
    rand: int = proto_field(7, default=0)
    # new_id: int = proto_field(12)


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
