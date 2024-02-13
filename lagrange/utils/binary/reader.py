from typing import Union

from typing_extensions import NewType

BYTES_LIKE = NewType("BYTES_LIKE", Union[bytes, bytearray, memoryview])


class Reader:
    def __init__(self, buffer: BYTES_LIKE):
        self._buffer: bytearray = buffer
        self._pos = 0

    @property
    def remain(self):
        return 0

    @remain.getter
    def get_remain(self) -> int:
        return len(self._buffer) - self._pos

    def read_u8(self) -> int:
        v = self._buffer[self._pos]
        self._pos += 1
        return v

    def read_bytes(self, length: int) -> bytes:
        v = self._buffer[self._pos:self._pos+length]
        self._pos += length
        return v
