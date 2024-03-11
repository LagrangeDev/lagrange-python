from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


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
    def build(cls, tgt: bytes) -> "HttpConn0x6ff":
        return cls(body=X501ReqBody(tgt_hex=tgt.hex()))


class ServerAddress(ProtoStruct):
    type: int = ProtoField(1)
    ip: int = ProtoField(2)
    port: int = ProtoField(3)
    area: int = ProtoField(4)


class ServerInfo(ProtoStruct):
    service_type: int = ProtoField(1)
    server_addrs: list[ServerAddress] = ProtoField(2, [])


class X501RspBody(ProtoStruct):
    sig_session: bytes = ProtoField(1)
    sig_key: bytes = ProtoField(2)
    servers: list[ServerInfo] = ProtoField(3, [])


class HttpConn0x6ffRsp(ProtoStruct):
    body: X501RspBody = ProtoField(0x501)
