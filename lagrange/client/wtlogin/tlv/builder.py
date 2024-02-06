import struct
from typing import Self, NewType, Union

BYTES_LIKE = NewType("BYTES_LIKE", Union[bytes, bytearray, memoryview])


class Builder:
    def __init__(self):
        self._buffer = bytearray()

    def __iadd__(self, other):
        if isinstance(other, (bytes, bytearray, memoryview)):
            self._buffer += other
        else:
            raise TypeError(
                f"buffer must be bytes or bytearray, not {type(other)}"
            )

    def __len__(self) -> int:
        return len(self._buffer)

    def _pack(self, struct_fmt: str, *args) -> Self:
        self._buffer += struct.pack(f">{struct_fmt}", *args)
        return self

    def pack(self) -> bytearray:
        return self._buffer

    def write_bool(self, v: bool) -> Self:
        return self._pack("?", v)

    def write_byte(self, v: int) -> Self:
        return self._pack("c", v)

    def write_bytes(self, v: BYTES_LIKE, with_length=False) -> Self:
        if with_length:
            self.write_u16(len(v))
        self._buffer += v
        return self

    def write_string(self, s: str) -> Self:
        return self.write_bytes(s.encode(), True)

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
