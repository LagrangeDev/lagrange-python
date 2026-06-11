import time
import json
from urllib import parse

from .httpcat import HttpCat
from .log import log

_logger = log.fork("sign_provider")

SIGN_PKG_LIST = [
    "trpc.o3.ecdh_access.EcdhAccess.SsoEstablishShareKey",
    "trpc.o3.ecdh_access.EcdhAccess.SsoSecureAccess",
    "trpc.o3.report.Report.SsoReport",
    "MessageSvc.PbSendMsg",
    "wtlogin.trans_emp",
    "wtlogin.login",
    "wtlogin.exchange_emp",
    "trpc.login.ecdh.EcdhService.SsoKeyExchange",
    "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLogin",
    "trpc.login.ecdh.EcdhService.SsoNTLoginEasyLogin",
    "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLoginNewDevice",
    "trpc.login.ecdh.EcdhService.SsoNTLoginEasyLoginUnusualDevice",
    "trpc.login.ecdh.EcdhService.SsoNTLoginPasswordLoginUnusualDevice",
    "trpc.login.ecdh.EcdhService.SsoNTLoginRefreshTicket",
    "trpc.login.ecdh.EcdhService.SsoNTLoginRefreshA2",
    "trpc.group.long_msg_interface.MsgService.SsoSendLongMsg",
    "trpc.group.long_msg_interface.MsgService.SsoRecvLongMsg",
    "OidbSvcTrpcTcp.0x11ec_1",
    "OidbSvcTrpcTcp.0x758_1",
    "OidbSvcTrpcTcp.0x7c1_1",
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
    "OidbSvcTrpcTcp.0x6d9_4",
]


def sign_provider(upstream_url: str, uin: int, guid: str, qua: str):
    purl = parse.urlparse(upstream_url)
    token = purl.username or None
    netloc = purl.hostname + (f":{purl.port}" if purl.port else "")
    url = parse.urlunparse(purl._replace(netloc=netloc))

    async def get_sign(cmd: str, seq: int, buf: bytes) -> dict:
        if cmd not in SIGN_PKG_LIST:
            return {}

        params = {
            "uin": uin,
            "command": cmd,
            "seq": seq,
            "body": buf.hex().lower(),
            "guid": guid.lower(),
            "qua": qua,
        }
        body = json.dumps(params).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        for _ in range(3):
            try:
                start_time = time.time()
                ret = await HttpCat.request("POST", url, body=body, header=headers)
                if ret.code != 200:
                    raise ConnectionError(ret.code, ret.body)
                _logger.debug(
                    f"signed for [{cmd}:{seq}]({(time.time() - start_time) * 1000:.2f}ms)"
                )
            except Exception:
                _logger.exception("Unexpected error on sign request:")
                continue
            break
        else:
            raise ConnectionError("Max retries exceeded")

        data = ret.json()
        code = data.get("code", 0)
        if code != 0:
            _logger.error(f"Sign server returned error: ({code}) {data.get('message')}")
            return {}

        value = data["value"]
        return {
            "sign": value["sec_sign"],
            "token": value["sec_token"],
            "extra": value["sec_extra"],
        }

    return get_sign
