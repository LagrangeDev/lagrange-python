from typing import Optional

from lagrange.utils.binary.protobuf import ProtoStruct, proto_field


class _LoginCookies(ProtoStruct, debug=True):
    str: str = proto_field(1)  # type: ignore


class _LoginVerify(ProtoStruct, debug=True):
    url: str = proto_field(3)


class _LoginErrField(ProtoStruct, debug=True):
    code: int = proto_field(1)
    title: str = proto_field(2)
    message: str = proto_field(3)


class _LoginRspHead(ProtoStruct, debug=True):
    account: dict = proto_field(1)  # {1: uin}
    device: dict = proto_field(
        2
    )  # {1: app.os, 2: device_name, 3: nt_login_type, 4: bytes(guid)}
    system: dict = proto_field(
        3
    )  # {1: device.kernel_version, 2: app.app_id, 3: app.package_name}
    error: Optional[_LoginErrField] = proto_field(4, default=None)
    cookies: Optional[_LoginCookies] = proto_field(5, default=None)


class _LoginCredentials(ProtoStruct, debug=True):
    credentials: Optional[bytes] = proto_field(1, default=None)  # on login request
    temp_pwd: Optional[bytes] = proto_field(3, default=None)
    tgt: Optional[bytes] = proto_field(4, default=None)
    d2: Optional[bytes] = proto_field(5, default=None)
    d2_key: Optional[bytes] = proto_field(6, default=None)


class _LoginRspBody(ProtoStruct, debug=True):
    credentials: Optional[_LoginCredentials] = proto_field(1, default=None)
    verify: Optional[_LoginVerify] = proto_field(2, default=None)


class NTLoginRsp(ProtoStruct, debug=True):
    head: _LoginRspHead = proto_field(1)
    body: Optional[_LoginRspBody] = proto_field(2, default=None)
