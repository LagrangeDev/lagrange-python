import struct
from typing import Optional

__all__ = ["qqtea_encrypt", "qqtea_decrypt"]


def _xor(a, b):
    op = 0xFFFFFFFF
    a1, a2 = struct.unpack(b">LL", a[0:8])
    b1, b2 = struct.unpack(b">LL", b[0:8])
    return struct.pack(b">LL", (a1 ^ b1) & op, (a2 ^ b2) & op)


def _tea_code(v, k) -> bytes:  # 传入8字节数据 16字节key
    n = 16
    op = 0xFFFFFFFF
    delta = 0x9E3779B9
    k = struct.unpack(b">LLLL", k[0:16])
    v0, v1 = struct.unpack(b">LL", v[0:8])
    sum_ = 0
    for i in range(n):
        sum_ += delta
        v0 += (op & (v1 << 4)) + k[0] ^ v1 + sum_ ^ (op & (v1 >> 5)) + k[1]
        v0 &= op
        v1 += (op & (v0 << 4)) + k[2] ^ v0 + sum_ ^ (op & (v0 >> 5)) + k[3]
        v1 &= op
    r = struct.pack(b">LL", v0, v1)
    return r


def _tea_decipher(v: bytes, k: bytes) -> bytes:
    n = 16
    op = 0xFFFFFFFF
    v0, v1 = struct.unpack(">LL", v[0:8])
    k0, k1, k2, k3 = struct.unpack(b">LLLL", k[0:16])
    delta = 0x9E3779B9
    sum_ = (delta << 4) & op  # 左移4位 就是x16
    for i in range(n):
        v1 -= ((v0 << 4) + k2) ^ (v0 + sum_) ^ ((v0 >> 5) + k3)
        v1 &= op
        v0 -= ((v1 << 4) + k0) ^ (v1 + sum_) ^ ((v1 >> 5) + k1)
        v0 &= op
        sum_ -= delta
        sum_ &= op
    return struct.pack(b">LL", v0, v1)


class _TEA:
    """
    QQ TEA 加解密, 64比特明码, 128比特密钥
    这是一个确认线程安全的独立加密模块，使用时必须要有一个全局变量secret_key，要求大于等于16位
    """

    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key

    @staticmethod
    def _preprocess(data: bytes) -> bytes:
        data_len = len(data)
        filln = (8 - (data_len + 2)) % 8 + 2
        fills = bytearray()
        for i in range(filln):
            fills.append(220)
        return bytes([(filln - 2) | 0xF8]) + fills + data + b"\x00" * 7

    def encrypt(self, data: bytes) -> bytes:
        data = self._preprocess(data)
        tr = b"\0" * 8
        to = b"\0" * 8
        result = bytearray()
        for i in range(0, len(data), 8):
            o = _xor(data[i : i + 8], tr)
            tr = _xor(_tea_code(o, self.secret_key), to)
            to = o
            result += tr
        return bytes(result)

    def decrypt(self, text: bytes) -> Optional[bytes]:  # v不可变
        data_len = len(text)
        plain = _tea_decipher(text, self.secret_key)
        pos = (plain[0] & 0x07) + 2
        ret = plain
        precrypt = text[0:8]
        for i in range(8, data_len, 8):
            x = _xor(
                _tea_decipher(_xor(text[i : i + 8], plain), self.secret_key), precrypt
            )  # 跳过了前8个字节
            plain = _xor(x, precrypt)
            precrypt = text[i : i + 8]
            ret += x
        if ret[-7:] != b"\0" * 7:
            return None
        return ret[pos + 1 : -7]


def qqtea_encrypt(data: bytes, key: bytes) -> bytes:
    return _TEA(key).encrypt(data)


def qqtea_decrypt(data: bytes, key: bytes) -> bytes:
    return _TEA(key).decrypt(data)


try:
    from ftea import TEA as FTEA

    def qqtea_encrypt(data: bytes, key: bytes) -> bytes:
        return FTEA(key).encrypt_qq(data)

    def qqtea_decrypt(data: bytes, key: bytes) -> bytes:
        return FTEA(key).decrypt_qq(data)

except ImportError:
    # Leave the pure Python version in place.
    pass
