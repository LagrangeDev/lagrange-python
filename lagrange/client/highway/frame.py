import struct
from typing import BinaryIO, Tuple

from lagrange.pb.highway.head import HighwayTransRespHead


def write_frame(head: bytes, body: bytes) -> bytes:
    buf = bytearray()
    buf.append(0x28)
    buf += struct.pack("!II", len(head), len(body))
    buf += head
    buf += body
    buf.append(0x29)
    return buf


def read_frame(
    reader: BinaryIO,
) -> Tuple[HighwayTransRespHead, bytes]:
    head = reader.read(9)
    if len(head) != 9 and head[0] != 0x28:
        raise ValueError("Invalid frame head", head)
    hl, bl = struct.unpack("!II", head[1:])
    try:
        return (
            HighwayTransRespHead.decode(reader.read(hl)),
            reader.read(bl),
        )
    finally:
        reader.read(1)  # flush end byte
