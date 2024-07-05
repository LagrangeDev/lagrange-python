import struct
from typing import Union

from typing_extensions import Optional, Self, TypeAlias

from lagrange.utils.crypto.tea import qqtea_encrypt

BYTES_LIKE: TypeAlias = Union[bytes, bytearray, memoryview]


class Builder:
    def __init__(self, encrypt_key: Optional[bytes] = None):
        self._buffer = bytearray()
        self._encrypt_key = encrypt_key

    def __iadd__(self, other):
        if isinstance(other, (bytes, bytearray, memoryview)):
            self._buffer += other
        else:
            raise TypeError(f"buffer must be bytes or bytearray, not {type(other)}")

    def __len__(self) -> int:
        return len(self._buffer)

    @property
    def buffer(self) -> bytearray:
        return self._buffer

    @property
    def data(self) -> bytes:
        if self._encrypt_key:
            return qqtea_encrypt(self._buffer, self._encrypt_key)
        return self.buffer

    def _pack(self, struct_fmt: str, *args) -> Self:
        self._buffer += struct.pack(f">{struct_fmt}", *args)
        return self

    def pack(self, typ: Optional[int] = None) -> bytes:
        if typ is not None:
            return struct.pack(">HH", typ, len(self.data)) + self.data
        return self.data

    def write_bool(self, v: bool) -> Self:
        return self._pack("?", v)

    def write_byte(self, v: int) -> Self:
        return self._pack("b", v)

    def write_bytes(self, v: BYTES_LIKE, *, with_length: bool = False) -> Self:
        if with_length:
            self.write_u16(len(v))
        self._buffer += v
        return self

    def write_string(self, s: str) -> Self:
        return self.write_bytes(s.encode(), with_length=True)

    def write_struct(self, struct_fmt: str, *args) -> Self:
        return self._pack(struct_fmt, *args)

    def write_u8(self, v: int) -> Self:
        return self._pack("B", v)

    def write_u16(self, v: int) -> Self:
        return self._pack("H", v)

    def write_u32(self, v: int) -> Self:
        return self._pack("I", v)

    def write_u64(self, v: int) -> Self:
        return self._pack("Q", v)

    def write_i8(self, v: int) -> Self:
        return self._pack("b", v)

    def write_i16(self, v: int) -> Self:
        return self._pack("h", v)

    def write_i32(self, v: int) -> Self:
        return self._pack("i", v)

    def write_i64(self, v: int) -> Self:
        return self._pack("q", v)

    def write_float(self, v: float) -> Self:
        return self._pack("f", v)

    def write_double(self, v: float) -> Self:
        return self._pack("d", v)

    def write_tlv(self, *tlvs: bytes) -> Self:
        self.write_u16(len(tlvs))
        for v in tlvs:
            self.write_bytes(v)
        return self
