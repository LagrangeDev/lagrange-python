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


class SendGrpBotHD(ProtoStruct):
    bot_id: int = proto_field(3)
    seq: int = proto_field(4, default=111111)  # nobody care
    B_id: str = proto_field(5, default="")  # set button_id
    B_data: str = proto_field(6, default="")  # set button_data
    IDD: int = proto_field(7, default=0)
    grp_id: int = proto_field(8, default=None)
    grp_type: int = proto_field(9, default=0)  # 0guild 1grp 2C2C(need grp_id==None)
