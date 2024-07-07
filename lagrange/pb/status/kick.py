from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class KickNT(ProtoStruct):
    uin: int = proto_field(1)
    tips: str = proto_field(3)
    title: str = proto_field(4)
