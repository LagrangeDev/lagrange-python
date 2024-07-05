from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .comm import CommonHead, IPv4, IPv6, MsgInfo, PicUrlExtInfo, VideoExtInfo


class MultiMediaRspHead(ProtoStruct):
    common: CommonHead = proto_field(1)
    ret_code: int = proto_field(2, default=0)
    msg: str = proto_field(3)


class RichMediaStorageTransInfo(ProtoStruct):
    sub_type: Optional[int] = proto_field(1, default=None)
    ext_type: int = proto_field(2)
    ext_value: bytes = proto_field(3)


class SubFileInfo(ProtoStruct):
    sub_type: int = proto_field(1)
    ukey: str = proto_field(2)
    ukey_ttl: int = proto_field(3)
    v4_addrs: list[IPv4] = proto_field(4)
    v6_addrs: list[IPv6] = proto_field(5)


class UploadRsp(ProtoStruct):
    ukey: Optional[str] = proto_field(1, default=None)  # None when file exists
    ukey_ttl: int = proto_field(2)
    v4_addrs: list[IPv4] = proto_field(3)
    v6_addrs: list[IPv6] = proto_field(4)
    msg_seq: int = proto_field(5, default=0)
    msg_info: MsgInfo = proto_field(6)
    ext: list[RichMediaStorageTransInfo] = proto_field(7, default=[])
    compat_qmsg: bytes = proto_field(8)
    sub_file_info: list[SubFileInfo] = proto_field(10, default=[])


class DownloadInfo(ProtoStruct):
    domain: str = proto_field(1)
    url_path: str = proto_field(2)
    https_port: Optional[int] = proto_field(3, default=None)
    v4_addrs: list[IPv4] = proto_field(4, default=[])
    v6_addrs: list[IPv6] = proto_field(5, default=[])
    pic_info: Optional[PicUrlExtInfo] = proto_field(6, default=None)
    video_info: Optional[VideoExtInfo] = proto_field(7, default=None)


class DownloadRsp(ProtoStruct):
    rkey: str = proto_field(1)
    rkey_ttl: Optional[int] = proto_field(2, default=None)
    info: DownloadInfo = proto_field(3)
    rkey_created_at: Optional[int] = proto_field(4, default=None)


class NTV2RichMediaResp(ProtoStruct):
    rsp_head: MultiMediaRspHead = proto_field(1)
    upload: Optional[UploadRsp] = proto_field(2, default=None)
    download: Optional[DownloadRsp] = proto_field(3, default=None)
