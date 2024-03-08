from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


class SendMsgRsp(ProtoStruct):
    ret_code: int = ProtoField(1)
    err_msg: str = ProtoField(2, "")
    grp_seq: int = ProtoField(11, 0)
    timestamp: int = ProtoField(12)
    private_seq: int = ProtoField(14, 0)

    @property
    def seq(self) -> int:
        return self.grp_seq or self.private_seq
