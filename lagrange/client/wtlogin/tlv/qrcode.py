from lagrange.utils.binary.builder import Builder


class QrCodeTlvBuilder(Builder):
    @classmethod
    def t11(cls, unusual_sign: bytes) -> bytes:
        return (
            cls()
            .write_bytes(unusual_sign)
        ).pack(0x11)

    @classmethod
    def t16(cls, sub_appid: int, appid_qrcode: int, guid: bytes, pt_version: str, package_name: str) -> bytes:
        return (
            cls()
            .write_u32(0)
            .write_u32(sub_appid)
            .write_u32(appid_qrcode)
            .write_bytes(guid)
            .write_string(package_name)
            .write_string(pt_version)
            .write_string(package_name)
        ).pack(0x16)

    @classmethod
    def t1b(cls) -> bytes:
        return cls().write_struct("8I", 0, 0, 3, 4, 72, 2, 2, 0).pack(0x18)

    @classmethod
    def t1d(cls, misc_bitmap: int) -> bytes:
        return (
            cls()
            .write_u8(1)
            .write_u32(misc_bitmap)
            .write_u32(0)
            .write_u8(0)
        ).pack(0x1d)

    @classmethod
    def t33(cls, guid: bytes) -> bytes:
        return cls().write_bytes(guid).pack(0x33)

    @classmethod
    def t35(cls, pt_os_version: int) -> bytes:
        return cls().write_u32(pt_os_version).pack(0x35)

    @classmethod
    def t66(cls, pt_os_version: int) -> bytes:
        return cls().write_u32(pt_os_version).pack(0x66)
