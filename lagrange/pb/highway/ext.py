from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .comm import IPv4, MsgInfoBody


def ipv4_to_network(ipv4: list[IPv4]) -> "NTHighwayNetwork":
    nets = []
    for v4 in ipv4:
        ip = v4.out_ip.to_bytes(4, byteorder="little")
        nets.append(
            NTHighwayIPv4(
                domain=NTHighwayDomain(ip=f"{ip[0]}.{ip[1]}.{ip[2]}.{ip[3]}"),
                port=v4.out_port,
            )
        )
    return NTHighwayNetwork(v4_addrs=nets)


class NTHighwayDomain(ProtoStruct):
    is_enable: bool = proto_field(1, default=True)
    ip: str = proto_field(2)


class NTHighwayIPv4(ProtoStruct):
    domain: NTHighwayDomain = proto_field(1)
    port: int = proto_field(2)


class NTHighwayNetwork(ProtoStruct):
    v4_addrs: list[NTHighwayIPv4] = proto_field(1)


class NTHighwayHash(ProtoStruct):
    sha1: bytes = proto_field(1)


class NTV2RichMediaHighwayExt(ProtoStruct):
    uuid: str = proto_field(1)
    ukey: str = proto_field(2)
    network: NTHighwayNetwork = proto_field(5)
    msg_info: list[MsgInfoBody] = proto_field(6)
    blk_size: int = proto_field(10)
    hash: NTHighwayHash = proto_field(11)

    @classmethod
    def build(
        cls,
        uuid: str,
        ukey: str,
        network: list[IPv4],
        msg_info: list[MsgInfoBody],
        blk_size: int,
        hash: bytes,
    ) -> "NTV2RichMediaHighwayExt":
        return cls(
            uuid=uuid,
            ukey=ukey,
            network=ipv4_to_network(network),
            msg_info=msg_info,
            blk_size=blk_size,
            hash=NTHighwayHash(sha1=hash),
        )
