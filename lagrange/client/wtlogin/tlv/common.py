import hashlib
import random

from lagrange.client.packet import PacketBuilder
from lagrange.info import AppInfo, DeviceInfo
from lagrange.utils.crypto.tea import qqtea_encrypt
from lagrange.utils.operator import timestamp


class CommonTlvBuilder(PacketBuilder):
    @classmethod
    def _rand_u32(cls) -> int:
        return random.randint(0x0, 0xFFFFFFFF)

    @classmethod
    def t18(
        cls,
        app_id: int,
        app_client_version: int,
        uin: int,
        _ping_version: int = 0,
        _sso_version: int = 5,
        unknown: int = 0,
    ) -> bytes:
        return (
            cls()
            .write_u16(_ping_version)
            .write_u32(_sso_version)
            .write_u32(app_id)
            .write_u32(app_client_version)
            .write_u32(uin)
            .write_u16(unknown)
            .write_u16(0)
        ).pack(0x18)

    @classmethod
    def t100(
        cls,
        sso_version: int,
        app_id: int,
        sub_app_id: int,
        app_client_version: int,
        sigmap: int,
        _db_buf_ver: int = 0,
    ) -> bytes:
        return (
            cls()
            .write_u16(_db_buf_ver)
            .write_u32(sso_version)
            .write_u32(app_id)
            .write_u32(sub_app_id)
            .write_u32(app_client_version)
            .write_u32(sigmap)
        ).pack(0x100)

    @classmethod
    def t106(
        cls,
        app_id: int,
        app_client_version: int,
        uin: int,
        password_md5: bytes,
        guid: str,
        tgtgt_key: bytes,
        ip: bytes = bytes(4),
        save_password: bool = True,
    ) -> bytes:
        key = hashlib.md5(
            password_md5 + bytes(4) + cls().write_u32(uin).pack()
        ).digest()

        body = (
            cls()
            .write_struct(
                "HIIIIQ",
                4,  # tgtgt version
                cls._rand_u32(),
                0,  # sso_version, depreciated
                app_id,
                app_client_version,
                uin,
            )
            .write_u32(timestamp() & 0xFFFFFFFF)
            .write_bytes(ip)
            .write_bool(save_password)
            .write_bytes(password_md5)
            .write_bytes(tgtgt_key)
            .write_u32(0)
            .write_bool(True)
            .write_bytes(bytes.fromhex(guid))
            .write_u32(0)
            .write_u32(1)
            .write_string(str(uin), "u16", False)
        ).pack()

        return cls().write_bytes(qqtea_encrypt(body, key), "u32").pack(0x106)

    @classmethod
    def t107(
        cls,
        pic_type: int = 1,
        cap_type: int = 0x0D,
        pic_size: int = 0,
        ret_type: int = 1,
    ) -> bytes:
        return (
            cls()
            .write_u16(pic_type)
            .write_u8(cap_type)
            .write_u16(pic_size)
            .write_u8(ret_type)
        ).pack(0x107)

    @classmethod
    def t116(cls, sub_sigmap: int) -> bytes:
        return (
            cls()
            .write_u8(0)
            .write_u32(12058620)  # unknown?
            .write_u32(sub_sigmap)
            .write_u8(0)
        ).pack(0x116)

    @classmethod
    def t124(cls) -> bytes:
        return cls().write_bytes(bytes(12)).pack(0x124)

    @classmethod
    def t128(cls, app_info_os: str, device_guid: bytes) -> bytes:
        return (
            cls()
            .write_u16(0)
            .write_u8(0)
            .write_u8(1)
            .write_u8(0)
            .write_u32(0)
            .write_string(app_info_os, "u16", False)
            .write_bytes(device_guid, "u16", False)
            .write_string("", "u16", False)
        ).pack(0x128)

    @classmethod
    def t141(
        cls,
        sim_info: bytes,
        apn: bytes = bytes(0),
    ) -> bytes:
        return (
            cls().write_bytes(sim_info, "u32", False).write_bytes(apn, "u32", False)
        ).pack(0x141)

    @classmethod
    def t142(cls, apk_id: str, _version: int = 0) -> bytes:
        return (cls().write_u16(_version).write_string(apk_id[:32], "u16", False)).pack(
            0x142
        )

    @classmethod
    def t144(cls, tgtgt_key: bytes, app_info: AppInfo, device: DeviceInfo) -> bytes:
        return (
            cls(tgtgt_key).write_tlv(
                cls.t16e(device.device_name),
                cls.t147(app_info.app_id, app_info.pt_version, app_info.package_name),
                cls.t128(app_info.os, bytes.fromhex(device.guid)),
                cls.t124(),
            )
        ).pack(0x144)

    @classmethod
    def t145(cls, guid: bytes) -> bytes:
        return (cls().write_bytes(guid)).pack(0x145)

    @classmethod
    def t147(cls, app_id: int, pt_version: str, package_name: str) -> bytes:
        return (
            cls()
            .write_u32(app_id)
            .write_string(pt_version, "u16", False)
            .write_string(package_name, "u16", False)
        ).pack(0x147)

    @classmethod
    def t166(cls, image_type: int) -> bytes:
        return (cls().write_byte(image_type)).pack(0x166)

    @classmethod
    def t16a(cls, no_pic_sig: bytes) -> bytes:
        return (cls().write_bytes(no_pic_sig)).pack(0x16A)

    @classmethod
    def t16e(cls, device_name: str) -> bytes:
        return (cls().write_bytes(device_name.encode())).pack(0x16E)

    @classmethod
    def t177(cls, sdk_version: str, build_time: int = 0) -> bytes:
        return (
            cls()
            .write_struct("BI", 1, build_time)
            .write_string(sdk_version, "u16", False)
        ).pack(0x177)

    @classmethod
    def t191(cls, can_web_verify: int = 0) -> bytes:
        return (cls().write_u8(can_web_verify)).pack(0x191)

    @classmethod
    def t318(cls, tgt_qr: bytes = bytes(0)) -> bytes:
        return (cls().write_bytes(tgt_qr)).pack(0x318)

    @classmethod
    def t521(cls, product_type: int = 0x13, product_desc: str = "basicim") -> bytes:
        return (
            cls().write_u32(product_type).write_string(product_desc, "u16", False)
        ).pack(0x521)
