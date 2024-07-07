from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class DataHighwayHead(ProtoStruct):
    version: int = proto_field(1, default=1)
    uin: Optional[str] = proto_field(2, default=None)
    command: Optional[str] = proto_field(3, default=None)
    seq: int = proto_field(4)
    retry_times: int = proto_field(5, default=0)
    app_id: int = proto_field(6)
    data_flag: int = proto_field(7, default=16)
    command_id: int = proto_field(8)
    build_ver: bytes = proto_field(9, default=bytes())


class SegHead(ProtoStruct):
    service_id: Optional[int] = proto_field(1, default=None)
    file_size: int = proto_field(2)
    data_offset: int = proto_field(3)
    data_length: int = proto_field(4)
    ret_code: int = proto_field(5, default=0)
    ticket: bytes = proto_field(6, default=bytes())
    md5: bytes = proto_field(8)
    file_md5: bytes = proto_field(9)
    cache_addr: Optional[int] = proto_field(10, default=None)
    cache_port: Optional[int] = proto_field(13, default=None)


class LoginSigHead(ProtoStruct):
    login_sig_type: int = proto_field(1)
    login_sig: bytes = proto_field(2, default=bytes())
    app_id: int = proto_field(3)


class HighwayTransReqHead(ProtoStruct):
    msg_head: Optional[DataHighwayHead] = proto_field(1, default=None)
    seg_head: Optional[SegHead] = proto_field(2, default=None)
    req_ext_info: bytes = proto_field(3, default=bytes())
    timestamp: int = proto_field(4)
    login_head: Optional[LoginSigHead] = proto_field(5, default=None)


class HighwayTransRespHead(ProtoStruct):
    msg_head: Optional[DataHighwayHead] = proto_field(1, default=None)
    seg_head: Optional[SegHead] = proto_field(2, default=None)
    err_code: int = proto_field(3)
    allow_retry: int = proto_field(4)
    cache_cost: Optional[int] = proto_field(5, default=None)
    ht_cost: Optional[int] = proto_field(6, default=None)
    ext_info: bytes = proto_field(7, default=bytes())
    timestamp: Optional[int] = proto_field(8, default=None)
    range: Optional[int] = proto_field(9, default=None)
    is_reset: Optional[int] = proto_field(10, default=None)
