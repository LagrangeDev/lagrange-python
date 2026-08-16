from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class ApplyUploadReqV3(ProtoStruct):
    sender_uid: str = proto_field(10)
    receiver_uid: str = proto_field(20)
    file_size: int = proto_field(30)
    file_name: str = proto_field(40)
    md5_10m: bytes = proto_field(50)
    sha1: bytes = proto_field(60)
    local_path: str = proto_field(70, default="/")
    md5: bytes = proto_field(110)
    sha3: bytes = proto_field(120, default=b"")


class E37UploadReq(ProtoStruct):
    command: int = proto_field(1, default=1700)
    seq: int = proto_field(2, default=0)
    upload: ApplyUploadReqV3 = proto_field(19)
    business_id: int = proto_field(101, default=3)
    client_type: int = proto_field(102, default=1)
    flag_support_media_platform: int = proto_field(200, default=1)

    @classmethod
    def build(cls, sender_uid: str, receiver_uid: str, file_size: int, file_name: str, md5_10m: bytes, sha1: bytes, md5: bytes) -> "E37UploadReq":
        return cls(
            upload=ApplyUploadReqV3(
                sender_uid=sender_uid,
                receiver_uid=receiver_uid,
                file_size=file_size,
                file_name=file_name,
                md5_10m=md5_10m,
                sha1=sha1,
                md5=md5,
            )
        )


class ApplyUploadRespV3(ProtoStruct):
    ret_code: int = proto_field(10, default=0)
    ret_msg: str = proto_field(20, default="")
    total_space: int = proto_field(30, default=0)
    used_space: int = proto_field(40, default=0)
    uploaded_size: int = proto_field(50, default=0)
    upload_ip: str = proto_field(60, default="")
    upload_domain: str = proto_field(70, default="")
    upload_port: int = proto_field(80, default=0)
    uuid: str = proto_field(90, default="")
    upload_key: bytes = proto_field(100, default=b"")
    bool_file_exist: bool = proto_field(110, default=False)
    pack_size: int = proto_field(120, default=0)
    upload_ip_list: list[str] = proto_field(130, default_factory=list)
    upload_https_port: int = proto_field(140, default=0)
    upload_https_domain: str = proto_field(150, default="")
    upload_dns: str = proto_field(160, default="")
    upload_lanip: str = proto_field(170, default="")
    file_addon: str = proto_field(200, default="")
    media_platform_upload_key: bytes = proto_field(220, default=b"")


class E37UploadRsp(ProtoStruct):
    command: int = proto_field(1, default=1700)
    seq: int = proto_field(2, default=0)
    upload: ApplyUploadRespV3 = proto_field(19)
    business_id: int = proto_field(101, default=3)
    client_type: int = proto_field(102, default=1)
    flag_support_media_platform: int = proto_field(200, default=1)


class E37DownloadBody(ProtoStruct):
    receiver_uid: str = proto_field(10)
    file_uuid: str = proto_field(20)
    type: int = proto_field(30, default=2)
    file_hash: str = proto_field(60)
    t2: int = proto_field(601, default=0)


class E37DownloadReq(ProtoStruct):
    sub_command: int = proto_field(1, default=1200)
    field2: int = proto_field(2, default=1)
    body: E37DownloadBody = proto_field(14)
    field101: int = proto_field(101, default=3)
    field102: int = proto_field(102, default=103)
    field200: int = proto_field(200, default=1)
    field99999: bytes = proto_field(99999, default=b"\xc0\x85\x2c\x01")

    @classmethod
    def build(cls, receiver_uid: str, file_uuid: str, file_hash: str) -> "E37DownloadReq":
        return cls(
            body=E37DownloadBody(
                receiver_uid=receiver_uid,
                file_uuid=file_uuid,
                file_hash=file_hash,
            )
        )


class E37DownloadResult(ProtoStruct):
    server: str = proto_field(20, default="")
    port: int = proto_field(40, default=0)
    url: str = proto_field(50, default="")
    additional_server: list[str] = proto_field(60, default_factory=list)
    sso_port: int = proto_field(80, default=0)
    sso_url: str = proto_field(90, default="")
    extra: bytes = proto_field(120, default=b"")


class E37DownloadRspBody(ProtoStruct):
    field10: int = proto_field(10, default=0)
    state: str = proto_field(20, default="")
    result: Optional[E37DownloadResult] = proto_field(30, default=None)
    metadata: Optional[dict] = proto_field(40, default=None)


class E37DownloadRsp(ProtoStruct):
    command: int = proto_field(1, default=0)
    sub_command: int = proto_field(2, default=0)
    body: Optional[E37DownloadRspBody] = proto_field(14, default=None)
    field50: int = proto_field(50, default=0)


class D6Upload(ProtoStruct):
    group_uin: int = proto_field(1)
    app_id: int = proto_field(2, default=7)
    bus_id: int = proto_field(3, default=102)
    entrance: int = proto_field(4, default=6)
    target_directory: str = proto_field(5)
    file_name: str = proto_field(6)
    local_directory: str = proto_field(7)
    file_size: int = proto_field(8)
    file_sha1: bytes = proto_field(9)
    file_sha3: bytes = proto_field(10, default=b"")
    file_md5: bytes = proto_field(11)
    field15: bool = proto_field(15, default=True)


class D6Download(ProtoStruct):
    group_uin: int = proto_field(1)
    app_id: int = proto_field(2, default=7)
    bus_id: int = proto_field(3, default=102)
    file_id: str = proto_field(4)


class D6Req(ProtoStruct):
    file: Optional[D6Upload] = proto_field(1, default=None)
    download: Optional[D6Download] = proto_field(3, default=None)


class D6UploadRsp(ProtoStruct):
    ret_code: int = proto_field(1, default=0)
    ret_msg: str = proto_field(2, default="")
    client_wording: str = proto_field(3, default="")
    upload_ip: str = proto_field(4, default="")
    server_dns: str = proto_field(5, default="")
    bus_id: int = proto_field(6, default=0)
    file_id: str = proto_field(7, default="")
    check_key: bytes = proto_field(8, default=b"")
    file_key: bytes = proto_field(9, default=b"")
    bool_file_exist: bool = proto_field(10, default=False)
    upload_ip_lan_v4: list[str] = proto_field(12, default_factory=list)
    upload_ip_lan_v6: list[str] = proto_field(13, default_factory=list)
    upload_port: int = proto_field(14, default=0)


class D6DownloadRsp(ProtoStruct):
    ret_code: int = proto_field(1, default=0)
    ret_msg: str = proto_field(2, default="")
    client_wording: str = proto_field(3, default="")
    download_ip: str = proto_field(4, default="")
    download_dns: str = proto_field(5, default="")
    download_url: bytes = proto_field(6, default=b"")
    file_sha1: bytes = proto_field(7, default=b"")
    file_sha3: bytes = proto_field(8, default=b"")
    file_md5: bytes = proto_field(9, default=b"")
    cookie_val: bytes = proto_field(10, default=b"")
    save_file_name: str = proto_field(11, default="")
    preview_port: int = proto_field(12, default=0)


class D6Rsp(ProtoStruct):
    upload: Optional[D6UploadRsp] = proto_field(1, default=None)
    download: Optional[D6DownloadRsp] = proto_field(3, default=None)


class D9SendFileInfo(ProtoStruct):
    busi_type: int = proto_field(1, default=102)
    file_id: str = proto_field(2)
    field3: int = proto_field(3)
    field4: Optional[str] = proto_field(4, default=None)
    field5: bool = proto_field(5, default=True)


class D9SendFileBody(ProtoStruct):
    group_uin: int = proto_field(1)
    type: int = proto_field(2, default=2)
    info: D9SendFileInfo = proto_field(3)


class D9SendFileReq(ProtoStruct):
    body: D9SendFileBody = proto_field(5)

    @classmethod
    def build(cls, group_uin: int, file_id: str) -> "D9SendFileReq":
        import random
        return cls(
            body=D9SendFileBody(
                group_uin=group_uin,
                info=D9SendFileInfo(file_id=file_id, field3=random.randint(0, 0xFFFFFFFF)),
            )
        )
