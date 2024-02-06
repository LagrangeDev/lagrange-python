import struct
import time
import random
from hashlib import md5
from typing import Union

from utils.binary import Packet
from utils.crypto.tea import qqtea_encrypt


class TlvEncoder:
    @classmethod
    def _pack_lv(cls, *data: Union[bytes, bytearray]) -> "Packet[()]":
        return Packet(struct.pack(">H", sum(map(len, data)))).write(*data)

    @classmethod
    def _pack_tlv(cls, type: int, *data: Union[bytes, bytearray]) -> "Packet[()]":
        return Packet(struct.pack(">HH", type, sum(map(len, data)))).write(*data)

    @classmethod
    def _pack_lv_limited(cls, data: Union[bytes, bytearray], size: int) -> "Packet[()]":
        return cls._pack_lv(data[:size])

    @classmethod
    def _random_int32(cls) -> int:
        return random.randint(0, 0xFFFFFFFF)

    @classmethod
    def t106(
            cls,
            app_id: int,
            app_client_version: int,
            uin: int,
            salt: int,
            password_md5: bytes,
            guid: bytes,
            tgtgt_key: bytes,
            ip: bytes = bytes(4),
            save_password: bool = True,
    ) -> "Packet[()]":
        key = md5(Packet.build(password_md5, bytes(4), struct.pack(">I", salt or uin))).digest()

        body = Packet.build(
            struct.pack(
                ">HIIIIIQ",
                4,  # tgtgt version
                cls._random_int32(),
                0,  # sso_version, depreciated
                app_id,
                app_client_version,
                uin or salt,
            ),
            struct.pack(">I", int(time.time())),
            ip,
            struct.pack(">?", save_password),
            struct.pack(">16s", password_md5),
            tgtgt_key,
            struct.pack(">I?", 0, bool(guid)),
            guid,
            struct.pack(">II", 1, 1),
            cls._pack_lv(str(uin).encode()),
        )

        data = qqtea_encrypt(bytes(body), key)
        return cls._pack_tlv(0x106, data)

    @classmethod
    def t142(cls, apk_id: str, _version: int = 0) -> "Packet[()]":
        return cls._pack_tlv(
            0x142,
            struct.pack(">H", _version),
            cls._pack_lv_limited(apk_id.encode(), 32),
        )

    @classmethod
    def t145(cls, guid: bytes) -> "Packet[()]":
        return cls._pack_tlv(0x145, guid)

    @classmethod
    def t18(
            cls,
            app_id: int,
            app_client_version: int,
            uin: int,
            _ping_version: int = 0,
            _sso_version: int = 5,
            unknown: int = 0,
    ) -> "Packet[()]":
        return cls._pack_tlv(
            0x18,
            struct.pack(
                ">HIIIIHH",
                _ping_version,
                _sso_version,
                app_id,
                app_client_version,
                uin,  # const 0
                unknown,
                0,
            ))

    @classmethod
    def t141(
            cls, sim_info: bytes, network_type: int = 0, apn: bytes = bytes(0), _version: int = 0
    ) -> "Packet[()]":
        return cls._pack_tlv(
            0x141,
            struct.pack(">H", _version),
            cls._pack_lv(sim_info),
            struct.pack(">H", network_type),
            cls._pack_lv(apn),
        )

    @classmethod
    def t177(cls, sdk_version: str, build_time: int = 0) -> "Packet[()]":
        return cls._pack_tlv(
            0x177,
            struct.pack(">BI", 1, build_time),
            cls._pack_lv(sdk_version.encode()),
        )

    @classmethod
    def t191(cls, can_web_verify: int = 0) -> "Packet[()]":
        return cls._pack_tlv(0x191, struct.pack(">B", can_web_verify))

    @classmethod
    def t100(
            cls,
            sso_version: int,
            app_id: int,
            sub_app_id: int,
            app_client_version: int,
            sigmap: int,
            _db_buf_ver: int = 0,
    ) -> "Packet[()]":
        return cls._pack_tlv(
            0x100,
            struct.pack(
                ">HIIIII",
                _db_buf_ver,
                sso_version,
                app_id,
                sub_app_id,
                app_client_version,
                sigmap,
            ),
        )

    @classmethod
    def t107(
            cls,
            pic_type: int = 1,
            cap_type: int = 0x0d,
            pic_size: int = 0,
            ret_type: int = 1,
    ) -> "Packet[()]":
        return cls._pack_tlv(0x107, struct.pack(">HBHB", pic_type, cap_type, pic_size, ret_type))

    @classmethod
    def t318(cls, tgt_qr: bytes = bytes(0)) -> "Packet[()]":
        return cls._pack_tlv(0x318, tgt_qr)

    @classmethod
    def t16a(cls, no_pic_sig: bytes) -> "Packet[()]":
        return cls._pack_tlv(0x16A, no_pic_sig)

    @classmethod
    def t166(cls, image_type: bytes) -> "Packet[()]":
        return cls._pack_tlv(0x166, struct.pack(">c", image_type))

    @classmethod
    def t521(cls, product_type: int = 0x13, product_desc: str = "basicim") -> "Packet[()]":
        return cls._pack_tlv(
            0x521,
            struct.pack(">I", product_type),
            cls._pack_lv(product_desc.encode()))
