import time
import json

from .httpcat import HttpCat
from .log import log

_logger = log.fork("sign_provider")

SIGN_PKG_LIST = [
    "trpc.o3.ecdh_access.EcdhAccess.SsoEstablishShareKey",
    "trpc.o3.ecdh_access.EcdhAccess.SsoSecureAccess",
    "trpc.o3.report.Report.SsoReport",
    "MessageSvc.PbSendMsg",
    # "wtlogin.trans_emp",
    "wtlogin.login",
    # "trpc.login.ecdh.EcdhService.SsoKeyExchange",
    "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLogin",
    "trpc.login.ecdh.EcdhService.SsoNTLoginEasyLogin",
    "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLoginNewDevice",
    "trpc.login.ecdh.EcdhService.SsoNTLoginEasyLoginUnusualDevice",
    "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLoginUnusualDevice",
    "OidbSvcTrpcTcp.0x11ec_1",
    "OidbSvcTrpcTcp.0x758_1",
    "OidbSvcTrpcTcp.0x7c2_5",
    "OidbSvcTrpcTcp.0x10db_1",
    "OidbSvcTrpcTcp.0x8a1_7",
    "OidbSvcTrpcTcp.0x89a_0",
    "OidbSvcTrpcTcp.0x89a_15",
    "OidbSvcTrpcTcp.0x88d_0",
    "OidbSvcTrpcTcp.0x88d_14",
    "OidbSvcTrpcTcp.0x112a_1",
    "OidbSvcTrpcTcp.0x587_74",
    "OidbSvcTrpcTcp.0x1100_1",
    "OidbSvcTrpcTcp.0x1102_1",
    "OidbSvcTrpcTcp.0x1103_1",
    "OidbSvcTrpcTcp.0x1107_1",
    "OidbSvcTrpcTcp.0x1105_1",
    "OidbSvcTrpcTcp.0xf88_1",
    "OidbSvcTrpcTcp.0xf89_1",
    "OidbSvcTrpcTcp.0xf57_1",
    "OidbSvcTrpcTcp.0xf57_106",
    "OidbSvcTrpcTcp.0xf57_9",
    "OidbSvcTrpcTcp.0xf55_1",
    "OidbSvcTrpcTcp.0xf67_1",
    "OidbSvcTrpcTcp.0xf67_5",
]


def sign_provider(upstream_url: str):
    async def get_sign(cmd: str, seq: int, buf: bytes) -> dict:
        if cmd not in SIGN_PKG_LIST:
            return {}

        params = {"cmd": cmd, "seq": seq, "src": buf.hex()}
        body = json.dumps(params).encode('utf-8')
        headers = {
            "Content-Type": "application/json"
        }
        start_time = time.time()
        ret = await HttpCat.request("POST", upstream_url, body=body, header=headers)
        _logger.debug(
            f"signed for [{cmd}:{seq}]({round((time.time() - start_time) * 1000, 2)}ms)"
        )
        if ret.code != 200:
            raise ConnectionError(ret.code, ret.body)

        return ret.json()["value"]

    return get_sign
