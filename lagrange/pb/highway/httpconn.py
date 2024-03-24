import ipaddress
from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class X501ReqBody(ProtoStruct):
    field_1: int = ProtoField(1, 0)
    field_2: int = ProtoField(2, 0)
    field_3: int = ProtoField(3, 16)
    field_4: int = ProtoField(4, 1)
    tgt_hex: str = ProtoField(5)
    field_6: int = ProtoField(6, 3)
    field_7: list[int] = ProtoField(7, [1, 5, 10, 21])
    field_9: int = ProtoField(9, 2)
    field_10: int = ProtoField(10, 9)
    field_11: int = ProtoField(11, 8)
    ver: str = ProtoField(15, "1.0.1")


class HttpConn0x6ffReq(ProtoStruct):
    body: X501ReqBody = ProtoField(0x501)

    @classmethod
    def build(cls, tgt: bytes) -> "HttpConn0x6ffReq":
        return cls(body=X501ReqBody(tgt_hex=tgt.hex()))


class BaseAddress(ProtoStruct):
    type: int = ProtoField(1)
    port: int = ProtoField(3)
    area: int = ProtoField(4, None)

    @property
    def ip(self) -> str:
        raise NotImplementedError


class ServerV4Address(BaseAddress):
    ip_int: int = ProtoField(2)

    @property
    def ip(self) -> str:
        return ipaddress.ip_address(self.ip_int).compressed


class ServerV6Address(BaseAddress):
    ip_bytes: bytes = ProtoField(2)  # 16 bytes v6_address

    @property
    def ip(self) -> str:
        return ipaddress.ip_address(self.ip_bytes).compressed


class ServerInfo(ProtoStruct):
    service_type: int = ProtoField(1)
    v4_addr: list[ServerV4Address] = ProtoField(2, [])
    v6_addr: list[ServerV6Address] = ProtoField(5, [])


class X501RspBody(ProtoStruct):
    sig_session: bytes = ProtoField(1)
    sig_key: bytes = ProtoField(2)
    servers: list[ServerInfo] = ProtoField(3, [])


class HttpConn0x6ffRsp(ProtoStruct):
    body: X501RspBody = ProtoField(0x501)
