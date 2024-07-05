from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class SendMsgRsp(ProtoStruct):
    ret_code: int = proto_field(1)
    err_msg: str = proto_field(2, default="")
    grp_seq: int = proto_field(11, default=0)
    timestamp: Optional[int] = proto_field(12, default=None)
    private_seq: int = proto_field(14, default=0)

    @property
    def seq(self) -> int:
        return self.grp_seq or self.private_seq
