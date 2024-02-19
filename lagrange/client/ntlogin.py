import json

from lagrange.info import AppInfo, DeviceInfo, SigInfo
from lagrange.utils.binary.protobuf import proto_encode, proto_decode
from lagrange.utils.crypto.aes import aes_gcm_encrypt, aes_gcm_decrypt
from .wtlogin.enum import LoginErrorCode


def build_ntlogin_captcha_submit(ticket: str, rand_str: str, aid: str):
    return {
        1: ticket,
        2: rand_str,
        3: aid
    }


def build_ntlogin_request(uin: int, app: AppInfo, device: DeviceInfo, sig: SigInfo, credential: bytes) -> bytes:
    body = {
        1: {
            1: {
                1: str(uin)
            },
            2: {
                1: app.os,
                2: device.device_name,
                3: app.nt_login_type,
                4: bytes.fromhex(device.guid)
            },
            3: {
                1: device.kernel_version,
                2: app.app_id,
                3: app.package_name
            }
        },
        2: {
            1: credential
        }
    }

    if sig.cookies:
        body[1][5] = {1: sig.cookies}
    if all(sig.captcha_info):
        print(*sig.captcha_info)
        body[2][2] = build_ntlogin_captcha_submit(*sig.captcha_info)

    return proto_encode({
        1: sig.key_sig,
        3: aes_gcm_encrypt(proto_encode(body), sig.exchange_key),
        4: 1
    })


def parse_ntlogin_response(response: bytes, sig: SigInfo) -> bool:
    frame = proto_decode(response, True)
    body = proto_decode(
        aes_gcm_decrypt(frame[3], sig.exchange_key)
    )

    if 1 in body[2]:
        cr = body[2][1]
        sig.tgt = cr[4]
        sig.d2 = cr[5]
        sig.d2_key = cr[6]
        sig.temp_pwd = cr[3]
        print("login successful")
        return True
    else:
        ret = LoginErrorCode(body[1][4][1])
        sig.cookies = body[1][5][1]
        if ret == LoginErrorCode.captcha_verify:
            verify_url: str = body[2][2][3].decode()
            aid = verify_url.split("&sid=")[1].split("&")[0]
            sig.captcha_info[2] = aid
            print("need captcha verify: " + verify_url)
        elif ret == LoginErrorCode.login_failure:
            stat = body[1][4]
            title = stat[2].decode()
            content = stat[3].decode()
            print(f"[{title}]: {content}")
        else:
            print(ret.name)

    return False
