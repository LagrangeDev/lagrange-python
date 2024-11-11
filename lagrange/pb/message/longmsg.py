from typing import Optional
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.utils.binary.protobuf.models import ProtoStruct, proto_field


class LongMsgCfg(ProtoStruct):
    f1: int = proto_field(1)
    f2: int = proto_field(2)
    f3: int = proto_field(3)
    f4: Optional[int] = proto_field(4, default=None)


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
        cfg = LongMsgCfg(f1=4, f2=1, f3=7, f4=0)
        if grp_id:
            return cls(msg_info=LongMsgBody.build_group(grp_id, msg_content), cfg=cfg)
        elif target:
            return cls(msg_info=LongMsgBody.build_friend(target, msg_content), cfg=cfg)
        else:
            raise ValueError("Must have target or grp_id")


class LongMsgActionBody(ProtoStruct):
    action_list: list[MsgPushBody] = proto_field(1)


class LongMsgAction(ProtoStruct):
    action_command: str = proto_field(1)
    action_data: LongMsgActionBody = proto_field(2)


class LongMsgResult(ProtoStruct):
    action: LongMsgAction = proto_field(2)
