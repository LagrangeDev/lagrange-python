import hashlib
import os

from lagrange.client.packet import PacketBuilder
from lagrange.info import AppInfo, DeviceInfo, SigInfo
from lagrange.utils.binary.protobuf import proto_decode, proto_encode
from lagrange.utils.binary.reader import Reader
from lagrange.utils.crypto.ecdh import ecdh
from lagrange.utils.crypto.tea import qqtea_decrypt, qqtea_encrypt
from lagrange.utils.log import log
from lagrange.utils.operator import timestamp


def build_code2d_packet(uin: int, cmd_id: int, app_info: AppInfo, body: bytes) -> bytes:
    """need build_uni_packet function to wrapper"""
    return build_login_packet(
        uin,
        "wtlogin.trans_emp",
        app_info,
        (
            PacketBuilder()
            .write_u8(0)
            .write_u16(len(body) + 53)
            .write_u32(app_info.app_id)
            .write_u32(0x72)
            .write_bytes(bytes(3))
            .write_u32(timestamp())
            .write_u8(2)
            .write_u16(len(body) + 49)
            .write_u16(cmd_id)
            .write_bytes(bytes(21))
            .write_u8(3)
            .write_u32(50)
            .write_bytes(bytes(14))
            .write_u32(app_info.app_id)
            .write_bytes(body)
        ).pack(),
    )


def build_login_packet(uin: int, cmd: str, app_info: AppInfo, body: bytes) -> bytes:
    enc_body = qqtea_encrypt(body, ecdh["secp192k1"].share_key)

    frame_body = (
        PacketBuilder()
        .write_u16(8001)
        .write_u16(2064 if cmd == "wtlogin.login" else 2066)
        .write_u16(0)
        .write_u32(uin)
        .write_u8(3)
        .write_u8(135)
        .write_u32(0)
        .write_u8(19)
        .write_u16(0)
        .write_u16(app_info.app_client_version)
        .write_u32(0)
        .write_u8(1)
        .write_u8(1)
        .write_bytes(bytes(16))
        .write_u16(0x102)
        .write_u16(len(ecdh["secp192k1"].public_key))
        .write_bytes(ecdh["secp192k1"].public_key)
        .write_bytes(enc_body)
        .write_u8(3)
    ).pack()

    frame = (
        PacketBuilder()
        .write_u8(2)
        .write_u16(len(frame_body) + 3)  # + 2 + 1
        .write_bytes(frame_body)
    ).pack()

    return frame


def build_uni_packet(
    uin: int,
    seq: int,
    cmd: str,
    sign: dict,
    app_info: AppInfo,
    device_info: DeviceInfo,
    sig_info: SigInfo,
    body: bytes,
) -> bytes:
    trace = f"00-{os.urandom(16).hex()}-{os.urandom(8).hex()}-01"

    head: dict = {15: trace, 16: sig_info.uid}
    if sign:
        head[24] = {
            1: bytes.fromhex(sign["sign"]),
            2: bytes.fromhex(sign["token"]),
            3: bytes.fromhex(sign["extra"]),
        }

    sso_header = (
        PacketBuilder()
        .write_u32(seq)
        .write_u32(app_info.sub_app_id)
        .write_u32(2052)  # locale id
        .write_bytes(bytes.fromhex("020000000000000000000000"))
        .write_bytes(sig_info.tgt, "u32")
        .write_string(cmd, "u32")
        .write_bytes(b"", "u32")
        .write_bytes(bytes.fromhex(device_info.guid), "u32")
        .write_bytes(b"", "u32")
        .write_string(app_info.current_version, "u16")
        .write_bytes(proto_encode(head), "u32")
    ).pack()

    sso_packet = (
        PacketBuilder().write_bytes(sso_header, "u32").write_bytes(body, "u32")
    ).pack()

    encrypted = qqtea_encrypt(sso_packet, sig_info.d2_key)

    service = (
        PacketBuilder()
        .write_u32(12)
        .write_u8(1 if sig_info.d2 else 2)
        .write_bytes(sig_info.d2, "u32")
        .write_u8(0)
        .write_string(str(uin), "u32")
        .write_bytes(encrypted)
    ).pack()

    return PacketBuilder().write_bytes(service, "u32").pack()


def decode_login_response(buf: bytes, sig: SigInfo):
    reader = Reader(buf)
    reader.read_bytes(2)
    typ = reader.read_u8()
    tlv = reader.read_tlv()

    if typ == 0:
        reader = Reader(qqtea_decrypt(tlv[0x119], sig.tgtgt))
        tlv = reader.read_tlv()
        sig.tgt = tlv.get(0x10A) or sig.tgt
        sig.d2 = tlv.get(0x143) or sig.d2
        sig.d2_key = tlv.get(0x305) or sig.d2_key
        sig.tgtgt = hashlib.md5(sig.d2_key).digest()
        sig.temp_pwd = tlv[0x106]
        sig.uid = proto_decode(tlv[0x543])[9][11][1].decode()  # type: ignore
        sig.info_updated()

        log.login.debug("SigInfo got")
        log.login.info("Login success, username: %s" % tlv[0x11A][5:].decode())

        return True
    elif 0x146 in tlv:
        err_buf = Reader(tlv[0x146])
        err_buf.read_bytes(4)
        title = err_buf.read_string(err_buf.read_u16())
        content = err_buf.read_string(err_buf.read_u16())
    elif 0x149 in tlv:
        err_buf = Reader(tlv[0x149])
        err_buf.read_bytes(2)
        title = err_buf.read_string(err_buf.read_u16())
        content = err_buf.read_string(err_buf.read_u16())
    else:
        title = "未知错误"
        content = "无法解析错误原因，请将完整日志提交给开发者"

    log.login.error(f"Login fail on oicq({hex(typ)}): [{title}]>{content}")

    return False
