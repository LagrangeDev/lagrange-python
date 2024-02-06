import struct

from client.wtlogin.TlvEncoder import TlvEncoder
from utils.binary import Packet


class TlvCodeEncoder(TlvEncoder):
    @classmethod
    def t11(cls, unusual_sign: bytes) -> "Packet[()]":
        return cls._pack_tlv(0x11, unusual_sign)

    @classmethod
    def t16(cls, sub_appid: int, appid_qrcode: int, guid: bytes, pt_version: str, package_name: str) -> "Packet[()]":
        return cls._pack_tlv(0x16, Packet.build(
            struct.pack(">III", 0, sub_appid, appid_qrcode),
            guid,
            cls._pack_lv(str(package_name).encode()),
            cls._pack_lv(pt_version.encode()),
            cls._pack_lv(str(package_name).encode())
        ))

    @classmethod
    def t18(cls) -> "Packet[()]":
        return cls._pack_tlv(0x18, struct.pack(">8I", 0, 0, 3, 4, 72, 2, 2, 0))

    @classmethod
    def t1d(cls, misc_bitmap: int) -> "Packet[()]":
        return cls._pack_tlv(0x18, struct.pack(">BIIB", 1, misc_bitmap, 0, 0))

    @classmethod
    def t33(cls, guid: bytes) -> "Packet[()]":
        return cls._pack_tlv(0x33, guid)

    @classmethod
    def t35(cls, pt_os_version: int) -> "Packet[()]":
        return cls._pack_tlv(0x35, struct.pack(">I", pt_os_version))

    @classmethod
    def t66(cls, pt_os_version: int) -> "Packet[()]":
        return cls._pack_tlv(0x66, struct.pack(">I", pt_os_version))
