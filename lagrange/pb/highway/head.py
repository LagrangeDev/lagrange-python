from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


class DataHighwayHead(ProtoStruct):
    version: int = ProtoField(1, 1)
    uin: str = ProtoField(2, None)
    command: str = ProtoField(3, None)
    seq: int = ProtoField(4)
    retry_times: int = ProtoField(5, 0)
    app_id: int = ProtoField(6)
    data_flag: int = ProtoField(7, 16)
    command_id: int = ProtoField(8)
    build_ver: bytes = ProtoField(9, bytes())


class SegHead(ProtoStruct):
    service_id: int = ProtoField(1, None)
    file_size: int = ProtoField(2)
    data_offset: int = ProtoField(3)
    data_length: int = ProtoField(4)
    ret_code: int = ProtoField(5, 0)
    ticket: bytes = ProtoField(6, bytes())
    md5: bytes = ProtoField(8)
    file_md5: bytes = ProtoField(9)
    cache_addr: int = ProtoField(10, None)
    cache_port: int = ProtoField(13, None)


class LoginSigHead(ProtoStruct):
    login_sig_type: int = ProtoField(1)
    login_sig: bytes = ProtoField(2, bytes())
    app_id: int = ProtoField(3)


class HighwayTransReqHead(ProtoStruct):
    msg_head: DataHighwayHead = ProtoField(1, None)
    seg_head: SegHead = ProtoField(2, None)
    req_ext_info: bytes = ProtoField(3, bytes())
    timestamp: int = ProtoField(4)
    login_head: LoginSigHead = ProtoField(5, None)


class HighwayTransRespHead(ProtoStruct):
    msg_head: DataHighwayHead = ProtoField(1, None)
    seg_head: SegHead = ProtoField(2, None)
    err_code: int = ProtoField(3)
    allow_retry: int = ProtoField(4)
    cache_cost: int = ProtoField(5, None)
    ht_cost: int = ProtoField(6, None)
    ext_info: bytes = ProtoField(7, bytes())
    timestamp: int = ProtoField(8, None)
    range: int = ProtoField(9, None)
    is_reset: int = ProtoField(10, None)

