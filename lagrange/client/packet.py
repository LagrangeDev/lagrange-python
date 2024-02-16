from typing_extensions import Literal, Self

from lagrange.utils.binary.builder import Builder, BYTES_LIKE

LENGTH_PREFIX = Literal["none", "u8", "u16", "u32", "u64"]


class PacketBuilder(Builder):
    def write_bytes(self, v: BYTES_LIKE, prefix: LENGTH_PREFIX = "none") -> Self:
        if prefix == "none":
            pass
        elif prefix == "u8":
            self.write_u8(len(v) + 1)
        elif prefix == "u16":
            self.write_u16(len(v) + 2)
        elif prefix == "u32":
            self.write_u32(len(v) + 4)
        elif prefix == "u64":
            self.write_u64(len(v) + 8)
        else:
            raise ArithmeticError("Invaild prefix")
        self._buffer += v
        return self

    def write_string(self, s: str, prefix: LENGTH_PREFIX = "u32") -> Self:
        return self.write_bytes(s.encode(), prefix)
