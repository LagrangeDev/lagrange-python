from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class ContentHead(ProtoStruct):
    type: int = ProtoField(1)
    sub_type: int = ProtoField(2, 0)
    msg_id: int = ProtoField(4, 0)
    seq: int = ProtoField(5, 0)
    timestamp: int = ProtoField(6, 0)
    rand: int = ProtoField(7, 0)
    # new_id: int = ProtoField(12)


class Grp(ProtoStruct):
    gid: int = ProtoField(1, 0)
    sender_name: str = ProtoField(4, "")  # empty in get_grp_msg
    grp_name: str = ProtoField(7, "")


class ResponseHead(ProtoStruct):
    from_uin: int = ProtoField(1, 0)
    from_uid: str = ProtoField(2, "")
    type: int = ProtoField(3, 0)
    sigmap: int = ProtoField(4, 0)
    to_uin: int = ProtoField(5, 0)
    to_uid: str = ProtoField(6, "")
    rsp_grp: Grp = ProtoField(8, None)
