from lagrange.utils.binary.protobuf import ProtoStruct, ProtoField


class _LoginCookies(ProtoStruct, debug=True):
    str: str = ProtoField(1)


class _LoginVerify(ProtoStruct, debug=True):
    url: str = ProtoField(3)


class _LoginErrField(ProtoStruct, debug=True):
    code: int = ProtoField(1)
    title: str = ProtoField(2)
    message: str = ProtoField(3)


class _LoginRspHead(ProtoStruct, debug=True):
    account: dict = ProtoField(1)  # {1: uin}
    device: dict = ProtoField(
        2
    )  # {1: app.os, 2: device_name, 3: nt_login_type, 4: bytes(guid)}
    system: dict = ProtoField(
        3
    )  # {1: device.kernel_version, 2: app.app_id, 3: app.package_name}
    error: _LoginErrField = ProtoField(4, None)
    cookies: _LoginCookies = ProtoField(5, None)


class _LoginCredentials(ProtoStruct, debug=True):
    credentials: bytes = ProtoField(1, None)  # on login request
    temp_pwd: bytes = ProtoField(3, None)
    tgt: bytes = ProtoField(4, None)
    d2: bytes = ProtoField(5, None)
    d2_key: bytes = ProtoField(6, None)


class _LoginRspBody(ProtoStruct, debug=True):
    credentials: _LoginCredentials = ProtoField(1, None)
    verify: _LoginVerify = ProtoField(2, None)


class NTLoginRsp(ProtoStruct, debug=True):
    head: _LoginRspHead = ProtoField(1)
    body: _LoginRspBody = ProtoField(2, None)
