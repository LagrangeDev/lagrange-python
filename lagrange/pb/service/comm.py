from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


class SendNudge(ProtoStruct):
    """
    retcode == 1005: no permission
    """
    to_dst1: int = ProtoField(1)
    to_grp: int = ProtoField(2)
    to_uin: int = ProtoField(5)
    field6: int = ProtoField(6, 0)
