from lagrange.info import AppInfo, DeviceInfo, SigInfo
from lagrange.utils.binary.protobuf import proto_decode, proto_encode
from lagrange.utils.crypto.aes import aes_gcm_decrypt, aes_gcm_encrypt
from lagrange.utils.log import log

from lagrange.client.wtlogin.enum import LoginErrorCode
from lagrange.pb.login.ntlogin import NTLoginRsp


def build_ntlogin_captcha_submit(ticket: str, rand_str: str, aid: str):
    return {1: ticket, 2: rand_str, 3: aid}


def build_ntlogin_request(
    uin: int,
    app: AppInfo,
    device: DeviceInfo,
    sig: SigInfo,
    captcha: list,
    credential: bytes,
) -> bytes:
    body = {
        1: {
            1: {1: str(uin)},
            2: {
                1: app.os,
                2: device.device_name,
                3: app.nt_login_type,
                4: bytes.fromhex(device.guid),
            },
            3: {1: device.kernel_version, 2: app.app_id, 3: app.package_name},
        },
        2: {1: credential},
    }

    if sig.cookies:
        body[1][5] = {1: sig.cookies}
    if all(captcha):
        log.login.debug("login with captcha info")
        body[2][2] = build_ntlogin_captcha_submit(*captcha)

    return proto_encode(
        {1: sig.key_sig, 3: aes_gcm_encrypt(proto_encode(body), sig.exchange_key), 4: 1}
    )


def parse_ntlogin_response(
    response: bytes, sig: SigInfo, captcha: list
) -> LoginErrorCode:
    frame = proto_decode(response, 0)
    rsp = NTLoginRsp.decode(aes_gcm_decrypt(frame[3], sig.exchange_key))

    if not rsp.head.error and rsp.body and rsp.body.credentials:
        cr = rsp.body.credentials
        sig.tgt = cr.tgt
        sig.d2 = cr.d2
        sig.d2_key = cr.d2_key
        sig.temp_pwd = cr.temp_pwd
        sig.info_updated()

        log.login.debug("SigInfo got")

        return LoginErrorCode.success
    else:
        ret = LoginErrorCode(rsp.head.error.code)
        if ret == LoginErrorCode.captcha_verify:
            sig.cookies = rsp.head.cookies.str
            verify_url = rsp.body.verify.url
            aid = verify_url.split("&sid=")[1].split("&")[0]
            captcha[2] = aid
            log.login.warning("need captcha verify: " + verify_url)
        else:
            stat = rsp.head.error
            title = stat.title
            content = stat.message
            log.login.error(
                f"Login fail on ntlogin({ret.name}): [{title}]>{content}"
            )

    return ret
