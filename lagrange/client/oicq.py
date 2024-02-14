import os
import time

from lagrange.info import DeviceInfo, AppInfo, SigInfo
from lagrange.utils.binary.builder import Builder
from lagrange.utils.binary.protobuf import proto_encode
from lagrange.utils.crypto.ecdh import ECDHSecp
from lagrange.utils.crypto.tea import qqtea_encrypt


def build_code2d_packet(
        uin: int,
        seq: int,
        cmd_id: int,
        app_info: AppInfo,
        device_info: DeviceInfo,
        sig_info: SigInfo,
        body: bytes
) -> bytes:
    return build_login_packet(
        uin,
        seq,
        "wtlogin.trans_emp",
        app_info,
        device_info,
        sig_info,
        (
            Builder()
            .write_u8(0)
            .write_u16(len(body) + 53)
            .write_u32(app_info.app_id)
            .write_u32(0x72)
            .write_bytes(bytes(3))
            .write_u32(int(time.time()))
            .write_u8(2)

            .write_u16(len(body) + 49)
            .write_u16(cmd_id)
            .write_bytes(bytes(21))
            .write_u8(3)
            .write_u32(50)
            .write_bytes(bytes(14))
            .write_u32(app_info.app_id)
            .write_bytes(body)
        ).pack()
    )


def build_login_packet(
        uin: int,
        seq: int,
        cmd: str,
        app_info: AppInfo,
        device_info: DeviceInfo,
        sig_info: SigInfo,
        body: bytes
) -> bytes:
    enc_body = qqtea_encrypt(body, ECDHSecp.share_key)

    frame_body = (
        Builder()
        .write_u16(8001)
        .write_u16(2066 if cmd == "wtlogin.login" else 2064)
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
        .write_bytes(ECDHSecp.client_public_key, True)
        .write_bytes(enc_body)
        .write_u8(3)
    ).pack()

    frame = (
        Builder()
        .write_u8(2)
        .write_u16(len(frame_body) + 3)  # + 2 + 1
        .write_bytes(frame_body)
    ).pack()

    return build_uni_packet(
        uin,
        seq,
        cmd,
        app_info,
        device_info,
        sig_info,
        frame
    )


def build_uni_packet(
        uin: int,
        seq: int,
        cmd: str,
        app_info: AppInfo,
        device_info: DeviceInfo,
        sig_info: SigInfo,
        body: bytes
) -> bytes:
    trace = f"00-{os.urandom(16).hex()}-{os.urandom(8).hex()}-01"
    head = proto_encode({
        15: trace,
        16: uin
    })

    sso_header = (
        Builder()
        .write_u32(seq)
        .write_u32(app_info.sub_app_id)
        .write_u32(2052)  # locale id
        .write_bytes(bytes.fromhex("020000000000000000000000"))
        .write_bytes(sig_info.tgt, True)
        .write_string(cmd)
        .write_bytes(b"", True)
        .write_string(device_info.guid)
        .write_u16(len(app_info.current_version) + 2)
        .write_bytes(app_info.current_version.encode())
        .write_bytes(head)
    ).pack()

    sso_packet = (
        Builder()
        .write_bytes(sso_header, True)
        .write_bytes(body, True)
    ).pack()

    encrypted = qqtea_encrypt(sso_packet, sig_info.d2_key)

    service = (
        Builder()
        .write_u32(12)
        .write_u8(2 if sig_info.d2 else 1)
        .write_bytes(sig_info.d2, True)
        .write_u8(0)
        .write_string(str(uin))
        .write_bytes(encrypted)
    ).pack()

    return Builder().write_bytes(service, True).pack()