from dataclasses import dataclass, field
from typing import List

from .serialize import BinarySerializer


@dataclass
class SigInfo(BinarySerializer):
    sequence: int
    tgtgt: bytes
    tgt: bytes
    d2: bytes
    d2_key: bytes
    qrsig: bytes

    exchange_key: bytes
    key_sig: bytes
    cookies: str
    unusual_sig: bytes
    temp_pwd: bytes
    uid: str
    captcha_info: List[str] = field(default_factory=lambda: ["", "", ""])

    @classmethod
    def new(cls, seq: int) -> "SigInfo":
        return cls(
            sequence=seq,
            tgtgt=bytes(),
            tgt=bytes(),
            d2=bytes(),
            d2_key=bytes(16),
            qrsig=bytes(),
            exchange_key=bytes(),
            key_sig=bytes(),
            cookies="",
            unusual_sig=bytes(),
            temp_pwd=bytes(),
            uid=""
        )
