from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class CommonHead(ProtoStruct):
    req_id: int = ProtoField(1, 1)
    cmd: int = ProtoField(2)


class PicExtInfo(ProtoStruct):
    biz_type: int = ProtoField(1, None)
    summary: str = ProtoField(2, None)
    c2c_reserved: bytes = ProtoField(11, bytes())
    troop_reserved: bytes = ProtoField(12, bytes())


class VideoExtInfo(ProtoStruct):
    from_scene: int = ProtoField(1, None)
    to_scene: int = ProtoField(2, None)
    pb_reserved: bytes = ProtoField(3, bytes())


class AudioExtInfo(ProtoStruct):
    src_uin: int = ProtoField(1, None)
    ptt_scene: int = ProtoField(2, None)
    ptt_type: int = ProtoField(3, None)
    change_voice: int = ProtoField(4, None)
    waveform: bytes = ProtoField(5, None)
    audio_convert_text: int = ProtoField(6, None)
    bytes_reserved: bytes = ProtoField(11, bytes())
    pb_reserved: bytes = ProtoField(12, bytes())
    general_flags: bytes = ProtoField(13, bytes())


class ExtBizInfo(ProtoStruct):
    pic: PicExtInfo = ProtoField(1, PicExtInfo())
    video: VideoExtInfo = ProtoField(2, VideoExtInfo())
    audio: AudioExtInfo = ProtoField(3, AudioExtInfo())
    bus_type: int = ProtoField(4, None)


class PicUrlExtInfo(ProtoStruct):
    origin_params: str = ProtoField(1)
    big_params: str = ProtoField(2)
    thumb_params: str = ProtoField(3)


class PicInfo(ProtoStruct):
    url_path: str = ProtoField(1)
    ext: PicUrlExtInfo = ProtoField(2)
    domain: str = ProtoField(3)


class FileType(ProtoStruct):
    type: int = ProtoField(1)
    pic_format: int = ProtoField(2, 0)
    video_format: int = ProtoField(3, 0)
    audio_format: int = ProtoField(4, 0)


class FileInfo(ProtoStruct):
    size: int = ProtoField(1, 0)
    hash: str = ProtoField(2)
    sha1: str = ProtoField(3)
    name: str = ProtoField(4)
    type: FileType = ProtoField(5)
    width: int = ProtoField(6, 0)
    height: int = ProtoField(7, 0)
    time: int = ProtoField(8, 0)
    is_origin: bool = ProtoField(9, True)


class IndexNode(ProtoStruct):
    info: FileInfo = ProtoField(1, None)
    file_uuid: str = ProtoField(2)
    store_id: int = ProtoField(3, None)
    upload_time: int = ProtoField(4, None)
    ttl: int = ProtoField(5, None)
    sub_type: int = ProtoField(6, None)


class MsgInfoBody(ProtoStruct):
    index: IndexNode = ProtoField(1)
    pic: PicInfo = ProtoField(2, None)
    video: dict = ProtoField(3, None)
    audio: dict = ProtoField(4, None)
    file_exists: bool = ProtoField(5, None)
    hashsum: bytes = ProtoField(6, b"")


class MsgInfo(ProtoStruct):
    body: list[MsgInfoBody] = ProtoField(1)
    biz_info: ExtBizInfo = ProtoField(2)


class IPv4(ProtoStruct):
    out_ip: int = ProtoField(1)
    out_port: int = ProtoField(2)
    in_ip: int = ProtoField(3)
    in_port: int = ProtoField(4)
    ip_type: int = ProtoField(5)


class IPv6(ProtoStruct):
    out_ip: bytes = ProtoField(1)
    out_port: int = ProtoField(2)
    in_ip: bytes = ProtoField(3, None)
    in_port: int = ProtoField(4, None)
    ip_type: int = ProtoField(5)
