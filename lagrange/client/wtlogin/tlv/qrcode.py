from lagrange.client.packet import PacketBuilder
from lagrange.utils.binary.protobuf import proto_encode


class QrCodeTlvBuilder(PacketBuilder):
    @classmethod
    def t11(cls, unusual_sign: bytes) -> bytes:
        return (cls().write_bytes(unusual_sign)).pack(0x11)

    @classmethod
    def t16(
        cls, appid: int, sub_appid: int, guid: bytes, pt_version: str, package_name: str
    ) -> bytes:
        return (
            cls()
            .write_u32(0)
            .write_u32(appid)
            .write_u32(sub_appid)
            .write_bytes(guid)
            .write_string(package_name, "u16", False)
            .write_string(pt_version, "u16", False)
            .write_string(package_name, "u16", False)
        ).pack(0x16)

    @classmethod
    def t1b(cls) -> bytes:
        return cls().write_struct("7IH", 0, 0, 3, 4, 72, 2, 2, 0).pack(0x1B)

    @classmethod
    def t1d(cls, misc_bitmap: int) -> bytes:
        return (cls().write_u8(1).write_u32(misc_bitmap).write_u32(0).write_u8(0)).pack(
            0x1D
        )

    @classmethod
    def t33(cls, guid: bytes) -> bytes:
        return cls().write_bytes(guid).pack(0x33)

    @classmethod
    def t35(cls, pt_os_version: int) -> bytes:
        return cls().write_u32(pt_os_version).pack(0x35)

    @classmethod
    def t66(cls, pt_os_version: int) -> bytes:
        return cls().write_u32(pt_os_version).pack(0x66)

    @classmethod
    def td1(cls, app_os: str, device_name: str) -> bytes:
        return (
            cls()
            .write_bytes(proto_encode({1: {1: app_os, 2: device_name}, 4: {6: 1}}))
            .pack(0xD1)
        )
