from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField
from .comm import CommonHead, FileInfo, ExtBizInfo, MsgInfo


class C2CUserInfo(ProtoStruct):
    account_type: int = ProtoField(1, 2)
    uid: str = ProtoField(2)


class GroupInfo(ProtoStruct):
    grp_id: int = ProtoField(1)


class ClientMeta(ProtoStruct):
    agent_type: int = ProtoField(1, 2)


class SceneInfo(ProtoStruct):
    req_type: int = ProtoField(101)
    bus_type: int = ProtoField(102)
    scene_type: int = ProtoField(200)
    c2c: C2CUserInfo = ProtoField(201, None)
    grp: GroupInfo = ProtoField(202, None)


class MultiMediaReqHead(ProtoStruct):
    common: CommonHead = ProtoField(1)
    scene: SceneInfo = ProtoField(2)
    meta: ClientMeta = ProtoField(3, ClientMeta())


class UploadInfo(ProtoStruct):
    file_info: FileInfo = ProtoField(1)
    sub_type: int = ProtoField(2)


class UploadReq(ProtoStruct):
    infos: list[UploadInfo] = ProtoField(1)
    try_fast_upload: bool = ProtoField(2, True)
    serve_sendmsg: bool = ProtoField(3, False)
    client_rand_id: int = ProtoField(4)
    compat_stype: int = ProtoField(5, 1)  # CompatQMsgSceneType
    biz_info: ExtBizInfo = ProtoField(6)
    client_seq: int = ProtoField(7, 0)
    no_need_compat_msg: bool = ProtoField(8, False)


class UploadCompletedReq(ProtoStruct):
    serve_sendmsg: bool = ProtoField(1)
    client_rand_id: int = ProtoField(2)
    msg_info: MsgInfo = ProtoField(3)
    client_seq: int = ProtoField(4)


class NTV2RichMediaReq(ProtoStruct):
    req_head: MultiMediaReqHead = ProtoField(1)
    upload: UploadReq = ProtoField(2, None)
    upload_completed: UploadCompletedReq = ProtoField(6, None)
    ext: bytes = ProtoField(99, None)
