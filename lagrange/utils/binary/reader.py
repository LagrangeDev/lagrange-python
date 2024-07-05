import struct
from typing import Any, Dict, Tuple, Union

from typing_extensions import TypeAlias, Literal

LENGTH_PREFIX = Literal["u8", "u16", "u32", "u64"]
BYTES_LIKE: TypeAlias = Union[bytes, bytearray, memoryview]


class Reader:
    def __init__(self, buffer: BYTES_LIKE):
        if not isinstance(buffer, (bytes, bytearray, memoryview)):
            raise TypeError("Invalid data: " + str(buffer))
        self._buffer = buffer
        self._pos = 0

    @property
    def remain(self) -> int:
        return len(self._buffer) - self._pos

    def read_u8(self) -> int:
        v = self._buffer[self._pos]
        self._pos += 1
        return v

    def read_u16(self) -> int:
        v = self._buffer[self._pos : self._pos + 2]
        self._pos += 2
        return struct.unpack(">H", v)[0]

    def read_u32(self) -> int:
        v = self._buffer[self._pos : self._pos + 4]
        self._pos += 4
        return struct.unpack(">I", v)[0]

    def read_u64(self) -> int:
        v = self._buffer[self._pos : self._pos + 8]
        self._pos += 8
        return struct.unpack(">Q", v)[0]

    def read_struct(self, format: str) -> Tuple[Any, ...]:
        size = struct.calcsize(format)
        v = self._buffer[self._pos : self._pos + size]
        self._pos += size
        return struct.unpack(format, v)

    def read_bytes(self, length: int) -> bytes:
        v = self._buffer[self._pos : self._pos + length]
        self._pos += length
        return v

    def read_string(self, length: int) -> str:
        return self.read_bytes(length).decode("utf-8")

    def read_bytes_with_length(self, prefix: LENGTH_PREFIX, with_prefix=True) -> bytes:
        if with_prefix:
            if prefix == "u8":
                length = self.read_u8() - 1
            elif prefix == "u16":
                length = self.read_u16() - 2
            elif prefix == "u32":
                length = self.read_u32() - 4
            else:
                length = self.read_u64() - 8
        else:
            if prefix == "u8":
                length = self.read_u8()
            elif prefix == "u16":
                length = self.read_u16()
            elif prefix == "u32":
                length = self.read_u32()
            else:
                length = self.read_u64()
        v = self._buffer[self._pos : self._pos + length]
        self._pos += length
        return v

    def read_string_with_length(self, prefix: LENGTH_PREFIX, with_prefix=True) -> str:
        return self.read_bytes_with_length(prefix, with_prefix).decode("utf-8")

    def read_tlv(self) -> Dict[int, bytes]:
        result = {}
        count = self.read_u16()

        for i in range(count):
            tag = self.read_u16()
            result[tag] = self.read_bytes(self.read_u16())

        return result
