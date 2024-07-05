from dataclasses import dataclass
from typing import BinaryIO

from .enum import AudioType


@dataclass
class AudioInfo:
    type: AudioType
    time: float

    @property
    def seconds(self) -> int:
        return int(self.time)


def _decode(f: BinaryIO, *, _f=False) -> AudioInfo:
    buf = f.read(1)
    if buf != b"\x23":
        if not _f:
            return _decode(f, _f=True)
        else:
            raise ValueError("Unknown audio type")
    else:
        buf += f.read(5)

    if buf == b"#!AMR\n":
        size = len(f.read())
        return AudioInfo(AudioType.amr, size / 1607.0)
    elif buf == b"#!SILK":
        ver = f.read(3)
        if ver != b"_V3":
            raise ValueError(f"Unsupported silk version: {ver}")
        data = f.read()
        size = len(data)

        if _f:  # txsilk
            typ = AudioType.tx_silk
        else:
            typ = AudioType.silk_v3

        blks = 0
        pos = 0
        while pos + 2 < size:
            length = int.from_bytes(data[pos : pos + 2], byteorder="little")
            if length == 0xFFFF:
                break
            else:
                blks += 1
                pos += length + 2

        return AudioInfo(typ, blks * 0.02)
    else:
        raise ValueError(f"Unknown audio type: {buf!r}")


def decode(f: BinaryIO) -> AudioInfo:
    try:
        return _decode(f)
    finally:
        f.seek(0)
