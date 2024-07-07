from typing import Optional
from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class SendNudge(ProtoStruct):
    """
    retcode == 1005: no permission
    """

    to_dst1: int = proto_field(1)
    to_grp: Optional[int] = proto_field(2)
    to_uin: Optional[int] = proto_field(5)
    field6: int = proto_field(6, default=0)
