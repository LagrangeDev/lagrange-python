import ipaddress
from typing import Optional

from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class X501ReqBody(ProtoStruct):
    field_1: int = proto_field(1, default=0)
    field_2: int = proto_field(2, default=0)
    field_3: int = proto_field(3, default=16)
    field_4: int = proto_field(4, default=1)
    tgt_hex: str = proto_field(5)
    field_6: int = proto_field(6, default=3)
    field_7: list[int] = proto_field(7, default=[1, 5, 10, 21])
    field_9: int = proto_field(9, default=2)
    field_10: int = proto_field(10, default=9)
    field_11: int = proto_field(11, default=8)
    ver: str = proto_field(15, default="1.0.1")


class HttpConn0x6ffReq(ProtoStruct):
    body: X501ReqBody = proto_field(0x501)

    @classmethod
    def build(cls, tgt: bytes) -> "HttpConn0x6ffReq":
        return cls(body=X501ReqBody(tgt_hex=tgt.hex()))


class BaseAddress(ProtoStruct):
    type: int = proto_field(1)
    port: int = proto_field(3)
    area: Optional[int] = proto_field(4, default=None)

    @property
    def ip(self) -> str:
        raise NotImplementedError


class ServerV4Address(BaseAddress):
    ip_int: int = proto_field(2)

    @property
    def ip(self) -> str:
        return ipaddress.ip_address(self.ip_int).compressed


class ServerV6Address(BaseAddress):
    ip_bytes: bytes = proto_field(2)  # 16 bytes v6_address

    @property
    def ip(self) -> str:
        return ipaddress.ip_address(self.ip_bytes).compressed


class ServerInfo(ProtoStruct):
    service_type: int = proto_field(1)
    v4_addr: list[ServerV4Address] = proto_field(2, default=[])
    v6_addr: list[ServerV6Address] = proto_field(5, default=[])


class X501RspBody(ProtoStruct):
    sig_session: bytes = proto_field(1)
    sig_key: bytes = proto_field(2)
    servers: list[ServerInfo] = proto_field(3, default=[])


class HttpConn0x6ffRsp(ProtoStruct):
    body: X501RspBody = proto_field(0x501)
