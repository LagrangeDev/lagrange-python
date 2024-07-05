from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class CommonHead(ProtoStruct):
    req_id: int = proto_field(1, default=1)
    cmd: int = proto_field(2)


class PicExtInfo(ProtoStruct):
    biz_type: Optional[int] = proto_field(1, default=None)
    summary: Optional[str] = proto_field(2, default=None)
    c2c_reserved: bytes = proto_field(11, default=bytes())
    troop_reserved: bytes = proto_field(12, default=bytes())


class VideoExtInfo(ProtoStruct):
    from_scene: Optional[int] = proto_field(1, default=None)
    to_scene: Optional[int] = proto_field(2, default=None)
    pb_reserved: bytes = proto_field(3, default=bytes())


class AudioExtInfo(ProtoStruct):
    src_uin: Optional[int] = proto_field(1, default=None)
    ptt_scene: Optional[int] = proto_field(2, default=None)
    ptt_type: Optional[int] = proto_field(3, default=None)
    change_voice: Optional[int] = proto_field(4, default=None)
    waveform: Optional[bytes] = proto_field(5, default=None)
    audio_convert_text: Optional[int] = proto_field(6, default=None)
    bytes_reserved: bytes = proto_field(11, default=bytes())
    pb_reserved: bytes = proto_field(12, default=bytes())
    general_flags: bytes = proto_field(13, default=bytes())


class ExtBizInfo(ProtoStruct):
    pic: PicExtInfo = proto_field(1, default=PicExtInfo())
    video: VideoExtInfo = proto_field(2, default=VideoExtInfo())
    audio: AudioExtInfo = proto_field(3, default=AudioExtInfo())
    bus_type: Optional[int] = proto_field(4, default=None)


class PicUrlExtInfo(ProtoStruct):
    origin_params: str = proto_field(1)
    big_params: str = proto_field(2)
    thumb_params: str = proto_field(3)


class PicInfo(ProtoStruct):
    url_path: str = proto_field(1)
    ext: PicUrlExtInfo = proto_field(2)
    domain: str = proto_field(3)


class FileType(ProtoStruct):
    type: int = proto_field(1)
    pic_format: int = proto_field(2, default=0)
    video_format: int = proto_field(3, default=0)
    audio_format: int = proto_field(4, default=0)


class FileInfo(ProtoStruct):
    size: int = proto_field(1, default=0)
    hash: str = proto_field(2)
    sha1: str = proto_field(3)
    name: str = proto_field(4)
    type: FileType = proto_field(5)
    width: int = proto_field(6, default=0)
    height: int = proto_field(7, default=0)
    time: int = proto_field(8, default=0)
    is_origin: bool = proto_field(9, default=True)


class IndexNode(ProtoStruct):
    info: Optional[FileInfo] = proto_field(1, default=None)
    file_uuid: str = proto_field(2)
    store_id: Optional[int] = proto_field(3, default=None)
    upload_time: Optional[int] = proto_field(4, default=None)
    ttl: Optional[int] = proto_field(5, default=None)
    sub_type: Optional[int] = proto_field(6, default=None)


class MsgInfoBody(ProtoStruct):
    index: IndexNode = proto_field(1)
    pic: Optional[PicInfo] = proto_field(2, default=None)
    video: Optional[dict] = proto_field(3, default=None)
    audio: Optional[dict] = proto_field(4, default=None)
    file_exists: Optional[bool] = proto_field(5, default=None)
    hashsum: bytes = proto_field(6, default=b"")


class MsgInfo(ProtoStruct):
    body: list[MsgInfoBody] = proto_field(1)
    biz_info: ExtBizInfo = proto_field(2)


class IPv4(ProtoStruct):
    out_ip: int = proto_field(1)
    out_port: int = proto_field(2)
    in_ip: int = proto_field(3)
    in_port: int = proto_field(4)
    ip_type: int = proto_field(5)


class IPv6(ProtoStruct):
    out_ip: bytes = proto_field(1)
    out_port: int = proto_field(2)
    in_ip: Optional[bytes] = proto_field(3, default=None)
    in_port: Optional[int] = proto_field(4, default=None)
    ip_type: int = proto_field(5)
