from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .comm import CommonHead, ExtBizInfo, FileInfo, MsgInfo, IndexNode


class C2CUserInfo(ProtoStruct):
    account_type: int = proto_field(1, default=2)
    uid: str = proto_field(2)


class GroupInfo(ProtoStruct):
    grp_id: int = proto_field(1)


class ClientMeta(ProtoStruct):
    agent_type: int = proto_field(1, default=2)


class SceneInfo(ProtoStruct):
    req_type: int = proto_field(101)
    bus_type: int = proto_field(102)
    scene_type: int = proto_field(200)
    c2c: Optional[C2CUserInfo] = proto_field(201, default=None)
    grp: Optional[GroupInfo] = proto_field(202, default=None)


class MultiMediaReqHead(ProtoStruct):
    common: CommonHead = proto_field(1)
    scene: SceneInfo = proto_field(2)
    meta: ClientMeta = proto_field(3, default=ClientMeta())


class UploadInfo(ProtoStruct):
    file_info: FileInfo = proto_field(1)
    sub_type: int = proto_field(2)


class UploadReq(ProtoStruct):
    infos: list[UploadInfo] = proto_field(1)
    try_fast_upload: bool = proto_field(2, default=True)
    serve_sendmsg: bool = proto_field(3, default=False)
    client_rand_id: int = proto_field(4)
    compat_stype: int = proto_field(5, default=1)  # CompatQMsgSceneType
    biz_info: ExtBizInfo = proto_field(6)
    client_seq: int = proto_field(7, default=0)
    no_need_compat_msg: bool = proto_field(8, default=False)


class UploadCompletedReq(ProtoStruct):
    serve_sendmsg: bool = proto_field(1)
    client_rand_id: int = proto_field(2)
    msg_info: MsgInfo = proto_field(3)
    client_seq: int = proto_field(4)


class DownloadVideoExt(ProtoStruct):
    busi_type: int = proto_field(1, default=0)
    scene_type: int = proto_field(2, default=0)
    sub_busi_type: Optional[int] = proto_field(3, default=None)


class DownloadExt(ProtoStruct):
    pic_ext: Optional[bytes] = proto_field(1, default=None)
    video_ext: DownloadVideoExt = proto_field(2, default=DownloadVideoExt())
    ptt_ext: Optional[bytes] = proto_field(3, default=None)


class DownloadReq(ProtoStruct):
    node: IndexNode = proto_field(1)
    ext: DownloadExt = proto_field(2, default=DownloadExt())


class NTV2RichMediaReq(ProtoStruct):
    req_head: MultiMediaReqHead = proto_field(1)
    upload: Optional[UploadReq] = proto_field(2, default=None)
    download: Optional[DownloadReq] = proto_field(3, default=None)
    upload_completed: Optional[UploadCompletedReq] = proto_field(6, default=None)
    ext: Optional[bytes] = proto_field(99, default=None)
