from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class KickNT(ProtoStruct):
    uin: int = ProtoField(1)
    tips: str = ProtoField(3)
    title: str = ProtoField(4)
