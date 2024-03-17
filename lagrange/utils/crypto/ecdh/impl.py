from .curve import CURVE
from .ecdh import ECDHProvider

ECDH_PRIME_PUBLIC = bytes.fromhex(
    "04"
    "9D1423332735980EDABE7E9EA451B3395B6F35250DB8FC56F25889F628CBAE3E"
    "8E73077914071EEEBC108F4E0170057792BB17AA303AF652313D17C1AC815E79"
)
ECDH_SECP_PUBLIC = bytes.fromhex(
    "04"
    "928D8850673088B343264E0C6BACB8496D697799F37211DE"
    "B25BB73906CB089FEA9639B4E0260498B51A992D50813DA8"
)


class BaseECDH:
    _provider: ECDHProvider
    _public_key: bytes
    _share_key: bytes
    _compress_key: bool

    @property
    def public_key(self) -> bytes:
        return self._public_key

    @property
    def share_key(self) -> bytes:
        return self._share_key

    def exchange(self, new_key: bytes):
        return self._provider.key_exchange(new_key, self._compress_key)


class ECDHPrime(BaseECDH):  # exchange key
    def __init__(self):
        self._provider = ECDHProvider(CURVE["prime256v1"])
        self._public_key = self._provider.pack_public(False)
        self._share_key = self._provider.key_exchange(ECDH_PRIME_PUBLIC, False)
        self._compress_key = False


class ECDHSecp(BaseECDH):  # login and others
    def __init__(self):
        self._provider = ECDHProvider(CURVE["secp192k1"])
        self._public_key = self._provider.pack_public(True)
        self._share_key = self._provider.key_exchange(ECDH_SECP_PUBLIC, True)
        self._compress_key = True


ecdh = {"secp192k1": ECDHSecp(), "prime256v1": ECDHPrime()}

__all__ = ["ecdh"]
