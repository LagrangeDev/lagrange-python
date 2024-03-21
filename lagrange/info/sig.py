from dataclasses import dataclass

from .serialize import BinarySerializer
from ..utils.operator import timestamp


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

    uin: int
    uid: str
    nickname: str
    last_update: int

    def info_updated(self):
        self.last_update = timestamp()

    @classmethod
    def new(cls, seq=8830) -> "SigInfo":
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
            uin=0,
            uid="",
            nickname="",
            last_update=0,
        )
