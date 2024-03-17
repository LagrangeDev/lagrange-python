import struct
from typing import Any, Tuple, Type, TypeVar, Union

from lagrange.utils.binary.types import *

P = TypeVar("P", bound="BasePacket")


class BasePacket(bytearray):
    """Base Packet Class.

    Provides basic operations like reading, writing by offset.

    Inherit from :class:`bytearray`
    """

    @classmethod
    def build(cls: Type[P], *data: Union[bytes, "BasePacket"]) -> P:
        """Build new packet and write data into it.

        Args:
            *data (Union[:obj:`bytes`, :obj:`Packet`]): Data to write

        Returns:
            :obj:`.Packet`: Current Packet
        """
        return cls().write(*data)

    def write(self: P, *data: Union[bytes, "BasePacket"]) -> P:
        """Write data into current packet.

        Args:
            *data (Union[:obj:`bytes`, :obj:`Packet`]): Data to write

        Returns:
            :obj:`.Packet`: Current Packet
        """
        for i in data:
            self.extend(i)
        return self

    def write_with_length(
        self: P, *data: Union[bytes, "BasePacket"], offset: int = 0
    ) -> P:
        """Write data into current packet with 4-byte length.

        Args:
            *data (Union[:obj:`bytes`, :obj:`Packet`]): Data to write
            offset (int): Length offset

        Returns:
            :obj:`.Packet`: Current Packet
        """
        self.extend(struct.pack(">I", sum(map(len, data)) + offset))
        return self.write(*data)

    def unpack(self, format: Union[bytes, str]) -> Tuple[Any, ...]:
        """Unpack all data from current packet.

        Args:
            format (Union[bytes, str]): Struct format.

        Returns:
            Tuple[Any, ...]: Unpacked data tuple.
        """
        return struct.unpack(format, self)

    def unpack_from(
        self, format: Union[bytes, str], offset: int = 0
    ) -> Tuple[Any, ...]:
        """Unpack data from current packet with given offset.

        Args:
            format (Union[bytes, str]): Struct format.
            offset (int, optional): Data offset. Defaults to 0.

        Returns:
            Tuple[Any, ...]: Unpacked data.
        """
        return struct.unpack_from(format, self, offset)

    def read_int8(self, offset: int = 0) -> INT8:
        return struct.unpack_from(">b", self, offset)[0]

    def read_uint8(self, offset: int = 0) -> UINT8:
        return struct.unpack_from(">B", self, offset)[0]

    def read_int16(self, offset: int = 0) -> INT16:
        return struct.unpack_from(">h", self, offset)[0]

    def read_uint16(self, offset: int = 0) -> UINT16:
        return struct.unpack_from(">H", self, offset)[0]

    def read_int32(self, offset: int = 0) -> INT32:
        return struct.unpack_from(">i", self, offset)[0]

    def read_uint32(self, offset: int = 0) -> UINT32:
        return struct.unpack_from(">I", self, offset)[0]

    def read_int64(self, offset: int = 0) -> INT64:
        return struct.unpack_from(">q", self, offset)[0]

    def read_uint64(self, offset: int = 0) -> UINT64:
        return struct.unpack_from(">Q", self, offset)[0]

    def read_byte(self, offset: int = 0) -> BYTE:
        return struct.unpack_from(">c", self, offset)[0]

    def read_bytes(self, n: int, offset: int = 0) -> BYTES:
        return struct.unpack_from(f">{n}s", self, offset)[0]

    def read_string(self, offset: int = 0) -> STRING:
        length = self.read_int32(offset) - 4
        return STRING(self.read_bytes(length, offset + 4).decode())
