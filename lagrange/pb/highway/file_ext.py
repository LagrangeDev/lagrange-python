from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class ExcitingUrlInfo(ProtoStruct):
    unknown: int = proto_field(1, default=1)
    host: str = proto_field(2)


class ExcitingHostInfo(ProtoStruct):
    url: ExcitingUrlInfo = proto_field(1)
    port: int = proto_field(2)


class ExcitingHostConfig(ProtoStruct):
    hosts: list[ExcitingHostInfo] = proto_field(200)


class ExcitingFileNameInfo(ProtoStruct):
    file_name: str = proto_field(100)


class ExcitingClientInfo(ProtoStruct):
    client_type: int = proto_field(100, default=3)
    app_id: str = proto_field(200, default="100")
    terminal_type: int = proto_field(300, default=3)
    client_ver: str = proto_field(400, default="1.1.1")
    unknown: int = proto_field(600, default=4)


class ExcitingFileEntry(ProtoStruct):
    file_size: int = proto_field(100)
    md5: bytes = proto_field(200)
    check_key: bytes = proto_field(300)
    md5_s2: bytes = proto_field(400)
    file_id: str = proto_field(600)
    upload_key: bytes = proto_field(700)


class ExcitingBusiInfo(ProtoStruct):
    bus_id: Optional[int] = proto_field(1, default=None)
    sender_uin: int = proto_field(100, default=0)
    receiver_uin: Optional[int] = proto_field(200, default=None)
    group_code: Optional[int] = proto_field(400, default=None)


class FileUploadEntry(ProtoStruct):
    busi_buff: ExcitingBusiInfo = proto_field(100)
    file_entry: ExcitingFileEntry = proto_field(200)
    client_info: ExcitingClientInfo = proto_field(300)
    file_name_info: ExcitingFileNameInfo = proto_field(400)
    host: ExcitingHostConfig = proto_field(500)


class FileUploadExt(ProtoStruct):
    unknown1: int = proto_field(1, default=100)
    unknown2: int = proto_field(2, default=1)
    unknown3: Optional[int] = proto_field(3, default=None)
    entry: FileUploadEntry = proto_field(100)
    unknown200: Optional[int] = proto_field(200, default=None)
