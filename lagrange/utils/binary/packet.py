import struct
from typing import Any, Callable, List

from lagrange.utils.binary.base import BasePacket
from lagrange.utils.binary.types import *


class Packet(BasePacket):
    """Packet Class for extracting data more efficiently.

    Support `PEP646`_ typing hints. Using ``pyright`` or ``pylance`` for type checking.

    Example:
        >>> packet = Packet(bytes.fromhex("01000233000000"))
        >>> packet.start().int8().uint16().bytes(4).execute()
        (1, 2, b'3\x00\x00\x00')

    . _PEP646:
        https://www.python.org/dev/peps/pep-0646/

    """

    def __init__(self, *args, **kwargs):
        super(Packet, self).__init__(*args, **kwargs)
        self.start()

    def _add_filter(self, filter: Callable[[Any], Any]):
        self._filters.append(filter)

    def _get_position(self) -> int:
        return struct.calcsize(self._query) + self._offset

    def start(self, offset: int = 0):
        self._query: str = ">"
        self._offset: int = offset
        self._executed: bool = False
        self._filters: List[Callable[[Any], Any]] = []
        return self

    def bool(self):
        self._query += "?"
        self._add_filter(BOOL)
        return self

    def int8(self):
        self._query += "b"
        self._add_filter(INT8)
        return self

    def uint8(self):
        self._query += "B"
        self._add_filter(UINT8)
        return self

    def int16(self):
        self._query += "h"
        self._add_filter(INT16)
        return self

    def uint16(self):
        self._query += "H"
        self._add_filter(UINT16)
        return self

    def int32(self):
        self._query += "i"
        self._add_filter(INT32)
        return self

    def uint32(self):
        self._query += "I"
        self._add_filter(UINT32)
        return self

    def int64(self):
        self._query += "q"
        self._add_filter(INT64)
        return self

    def uint64(self):
        self._query += "Q"
        self._add_filter(UINT64)
        return self

    def float(self):
        self._query += "f"
        self._add_filter(FLOAT)
        return self

    def double(self):
        self._query += "d"
        self._add_filter(DOUBLE)
        return self

    def byte(self):
        self._query += "c"
        self._add_filter(BYTE)
        return self

    def bytes(self, length: int):
        self._query += f"{length}s"
        self._add_filter(BYTES)
        return self

    def bytes_with_length(self, head_bytes: int, offset: int = 0):
        length = int.from_bytes(
            self.read_bytes(head_bytes, self._get_position()),
            "big",
        )
        self._query += f"{head_bytes}x{length - offset}s"
        self._add_filter(BYTES)
        return self

    def string(self, head_bytes: int, offset: int = 0, encoding: str = "utf-8"):
        length = int.from_bytes(
            self.read_bytes(head_bytes, self._get_position()),
            "big",
        )
        self._query += f"{head_bytes}x{length - offset}s"
        self._add_filter(lambda x: STRING(x.decode(encoding)))
        return self

    def offset(self, offset: int):
        self._query += f"{offset}x"
        return self

    def remain(self):
        length = struct.calcsize(self._query)
        self._query += f"{len(self) - length}s"
        self._add_filter(Packet)
        return self

    def execute(self):
        if self._executed:
            raise RuntimeError("Cannot re-execute query. Call `start()` first.")

        query = self._query
        filters = self._filters
        self._query = ">"
        self._filters = []
        self._executed = True
        return tuple(
            map(
                lambda f, v: f(v),
                filters,
                self.unpack_from(query, self._offset),
            )
        )
