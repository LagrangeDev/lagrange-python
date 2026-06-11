from typing import Optional
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.utils.binary.protobuf.models import ProtoStruct, proto_field


class LongMsgCfg(ProtoStruct):
    sub_cmd: int = proto_field(1)
    client_type: int = proto_field(2, default=0)
    platform: int = proto_field(3, default=0)
    proxy_type: Optional[int] = proto_field(4, default=None)


class LongMsgRespResult(ProtoStruct):
    resid: str = proto_field(3)


class LongMsgResp(ProtoStruct):
    result: LongMsgRespResult = proto_field(2)
    cfg: LongMsgCfg = proto_field(15)


class MulitMsgProperty(ProtoStruct):
    value: str = proto_field(2)  # uid or grp_id


class LongMsgBody(ProtoStruct):
    f1: int = proto_field(1)  # grp 3,friend 1
    gid_or_uid: MulitMsgProperty = proto_field(2)
    grp_id: Optional[int] = proto_field(3, default=None)
    msg_content: bytes = proto_field(4)

    @classmethod
    def build_friend(cls, target: str, msg_content: bytes):
        return cls(f1=1, gid_or_uid=MulitMsgProperty(value=target), msg_content=msg_content)

    @classmethod
    def build_group(cls, grp_id: int, msg_content: bytes):
        return cls(f1=3, gid_or_uid=MulitMsgProperty(value=str(grp_id)), grp_id=grp_id, msg_content=msg_content)


class LongMsgRsp(ProtoStruct):
    msg_info: LongMsgBody = proto_field(2)
    cfg: LongMsgCfg = proto_field(15)

    @classmethod
    def build(cls, msg_content: bytes, target: str = "", grp_id: Optional[int] = None):
        cfg = LongMsgCfg(sub_cmd=4, client_type=1, platform=7, proxy_type=0)
        if grp_id:
            return cls(msg_info=LongMsgBody.build_group(grp_id, msg_content), cfg=cfg)
        elif target:
            return cls(msg_info=LongMsgBody.build_friend(target, msg_content), cfg=cfg)
        else:
            raise ValueError("Must have target or grp_id")


class PbMultiMsgNew(ProtoStruct):
    msg: list[MsgPushBody] = proto_field(1)


class PbMultiMsgItem(ProtoStruct):
    file_name: str = proto_field(1)
    buffer: PbMultiMsgNew = proto_field(2)


class PbMultiMsgTransmit(ProtoStruct):
    messages: list[MsgPushBody] = proto_field(1, default_factory=list)
    items: list[PbMultiMsgItem] = proto_field(2)


class LongMsgActionBody(ProtoStruct):
    action_list: list[MsgPushBody] = proto_field(1)


class LongMsgAction(ProtoStruct):
    action_command: str = proto_field(1) # 接收时也可能是uniseq
    action_data: LongMsgActionBody = proto_field(2)


class LongMsgResult(ProtoStruct):
    action: list[LongMsgAction] = proto_field(2)


class RecvLongMsgInfo(ProtoStruct):
    uid: MulitMsgProperty = proto_field(1)
    res_id: str = proto_field(2)
    msg_type: int = proto_field(3, default=1)


class RecvLongMsgReq(ProtoStruct):
    info: RecvLongMsgInfo = proto_field(1)
    settings: LongMsgCfg = proto_field(15)

    @classmethod
    def build(cls, uid: str, res_id: str):
        return cls(
            info=RecvLongMsgInfo(uid=MulitMsgProperty(value=uid), res_id=res_id),
            settings=LongMsgCfg(sub_cmd=2, client_type=0, platform=0, proxy_type=0),
        )


class RecvLongMsgResult(ProtoStruct):
    res_id: str = proto_field(3)
    payload: bytes = proto_field(4)


class RecvLongMsgRsp(ProtoStruct):
    result: RecvLongMsgResult = proto_field(1)
    settings: LongMsgCfg = proto_field(15)
