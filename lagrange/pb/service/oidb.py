from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


class OidbRequest(ProtoStruct):
    cmd: int = ProtoField(1)
    sub_cmd: int = ProtoField(2)
    data: bytes = ProtoField(4)
    is_uid: bool = ProtoField(12, False)


class OidbResponse(OidbRequest):
    ret_code: int = ProtoField(3)
    err_msg: str = ProtoField(5)
