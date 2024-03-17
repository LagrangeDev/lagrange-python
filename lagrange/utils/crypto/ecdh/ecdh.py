import hashlib
import math
import random

from .curve import EllipticCurve, EllipticPoint


class ECDHProvider:
    def __init__(self, curve: EllipticCurve):
        self._curve = curve
        self._secret = self._create_secret()
        self._public = self._create_public(self._secret)

    def key_exchange(self, bob_pub: bytes, hashed: bool) -> bytes:
        unpacked = self.unpack_public(bob_pub)
        shared = self._create_shared(self._secret, unpacked)
        return self._pack_shared(shared, hashed)

    def unpack_public(self, pub: bytes) -> EllipticPoint:
        length = len(pub)
        if length != self._curve.size * 2 + 1 and length != self._curve.size + 1:
            raise AssertionError("Length of public key does not match")

        x = bytes(1) + pub[1 : self._curve.size + 1]
        if pub[0] == 0x04:  # uncompressed
            y = bytes(1) + pub[self._curve.size + 1 : self._curve.size * 2 + 1]
            return EllipticPoint(int.from_bytes(x, "big"), int.from_bytes(y, "big"))

        px = int.from_bytes(x, "big")
        x_3 = pow(px, 3) % self._curve.P
        ax = px * self._curve.P
        right = (x_3 + ax + self._curve.B) % self._curve.P

        tmp = (self._curve.P + 1) >> 2
        py = pow(right, tmp, self._curve.P)

        if py % 2 == 0:
            tmp = self._curve.P
            tmp -= py
            py = tmp

        return EllipticPoint(px, py)

    def pack_public(self, compress: bool) -> bytes:
        if compress:
            result = bytearray(self._public.x.to_bytes(self._curve.size, "big"))
            result = bytearray(1) + result
            result[0] = (
                0x02
                if (((self._public.y % 2) == 0) ^ ((self._public.y > 0) < 0))
                else 0x03
            )
            return result

        x = self._public.x.to_bytes(self._curve.size, "big")
        y = self._public.y.to_bytes(self._curve.size, "big")
        result = bytearray(1) + x + y
        result[0] = 0x04
        return bytes(result)

    def _pack_shared(self, shared: EllipticPoint, hashed: bool) -> bytes:
        x = shared.x.to_bytes(self._curve.size, "big")
        if hashed:
            x = hashlib.md5(x[0 : self._curve.pack_size]).digest()
        return x

    def _create_public(self, sec: int) -> EllipticPoint:
        return self._create_shared(sec, self._curve.G)

    def _create_secret(self) -> int:
        result = 0

        while result < 1 or result >= self._curve.N:
            buffer = bytearray(random.Random().randbytes(self._curve.size + 1))
            buffer[self._curve.size] = 0
            result = int.from_bytes(buffer, "little")

        return result

    def _create_shared(self, sec: int, pub: EllipticPoint) -> EllipticPoint:
        if sec % self._curve.N == 0 or pub.is_default:
            return EllipticPoint(0, 0)  # default
        if sec < 0:
            self._create_shared(-sec, -pub)

        if not self._curve.check_on(pub):
            raise AssertionError("Incorrect public key")

        pr = EllipticPoint(0, 0)
        pa = pub
        while sec > 0:
            if (sec & 1) > 0:
                pr = _point_add(self._curve, pr, pa)

            pa = _point_add(self._curve, pa, pa)
            sec >>= 1

        if not self._curve.check_on(pr):
            raise AssertionError("Incorrect result assertion")
        return pr


def _point_add(
    curve: EllipticCurve, p1: EllipticPoint, p2: EllipticPoint
) -> EllipticPoint:
    if p1.is_default:
        return p2
    if p2.is_default:
        return p1
    if not (curve.check_on(p1) and curve.check_on(p2)):
        raise AssertionError("Points is not on the curve")

    if p1.x == p2.x:
        if p1.y == p2.y:
            m = (3 * p1.x * p1.x + curve.A) * _mod_inverse(p1.y << 1, curve.P)
        else:
            return EllipticPoint(0, 0)  # default
    else:
        m = (p1.y - p2.y) * _mod_inverse(p1.x - p2.x, curve.P)

    xr = _mod(m * m - p1.x - p2.x, curve.P)
    yr = _mod(m * (p1.x - xr) - p1.y, curve.P)
    pr = EllipticPoint(xr, yr)

    if not curve.check_on(pr):
        raise AssertionError("Result point is not on the curve")
    return pr


def _mod(a: int, b: int) -> int:
    result = a % b
    if result < 0:
        result += b
    return result


def _mod_inverse(a: int, p: int) -> int:
    if a < 0:
        return p - _mod_inverse(-a, p)

    g = math.gcd(a, p)
    if g != 1:
        raise AssertionError("Inverse does not exist.")

    return pow(a, p - 2, p)
