from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct

from .comm import CommonHead, IPv4, IPv6, MsgInfo, PicUrlExtInfo, VideoExtInfo


class MultiMediaRspHead(ProtoStruct):
    common: CommonHead = ProtoField(1)
    ret_code: int = ProtoField(2, 0)
    msg: str = ProtoField(3)


class RichMediaStorageTransInfo(ProtoStruct):
    sub_type: int = ProtoField(1, None)
    ext_type: int = ProtoField(2)
    ext_value: bytes = ProtoField(3)


class SubFileInfo(ProtoStruct):
    sub_type: int = ProtoField(1)
    ukey: str = ProtoField(2)
    ukey_ttl: int = ProtoField(3)
    v4_addrs: list[IPv4] = ProtoField(4)
    v6_addrs: list[IPv6] = ProtoField(5)


class UploadRsp(ProtoStruct):
    ukey: str = ProtoField(1, None)  # None when file exists
    ukey_ttl: int = ProtoField(2)
    v4_addrs: list[IPv4] = ProtoField(3)
    v6_addrs: list[IPv6] = ProtoField(4)
    msg_seq: int = ProtoField(5, 0)
    msg_info: MsgInfo = ProtoField(6)
    ext: list[RichMediaStorageTransInfo] = ProtoField(7, [])
    compat_qmsg: bytes = ProtoField(8)
    sub_file_info: list[SubFileInfo] = ProtoField(10, [])


class DownloadInfo(ProtoStruct):
    domain: str = ProtoField(1)
    url_path: str = ProtoField(2)
    https_port: int = ProtoField(3, None)
    v4_addrs: list[IPv4] = ProtoField(4, [])
    v6_addrs: list[IPv6] = ProtoField(5, [])
    pic_info: PicUrlExtInfo = ProtoField(6, None)
    video_info: VideoExtInfo = ProtoField(7, None)


class DownloadRsp(ProtoStruct):
    rkey: str = ProtoField(1)
    rkey_ttl: int = ProtoField(2, None)
    info: DownloadInfo = ProtoField(3)
    rkey_created_at: int = ProtoField(4, None)


class NTV2RichMediaResp(ProtoStruct):
    rsp_head: MultiMediaRspHead = ProtoField(1)
    upload: UploadRsp = ProtoField(2, None)
    download: DownloadRsp = ProtoField(3, None)
