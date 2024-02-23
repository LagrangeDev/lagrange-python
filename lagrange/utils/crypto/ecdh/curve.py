from .point import EllipticPoint


class EllipticCurve:
    def __init__(self, P: int, A: int, B: int, G: EllipticPoint, N: int, H: int, size: int, pack_size: int):
        self._P = P
        self._A = A
        self._B = B
        self._G = G
        self._N = N
        self._H = H
        self._size = size
        self._pack_size = pack_size

    @property
    def P(self) -> int:
        return self._P

    @property
    def A(self) -> int:
        return self._A

    @property
    def B(self) -> int:
        return self._B

    @property
    def G(self) -> EllipticPoint:
        return self._G

    @property
    def N(self) -> int:
        return self._N

    @property
    def size(self) -> int:
        return self._size

    @property
    def pack_size(self) -> int:
        return self._pack_size

    def check_on(self, point: EllipticPoint) -> bool:
        return (pow(point.y, 2) - pow(point.x, 3) - self._A * point.x - self._B) % self._P == 0


CURVE = {
    "secp192k1": EllipticCurve(
        0xfffffffffffffffffffffffffffffffffffffffeffffee37,
        0,
        3,
        EllipticPoint(0xdb4ff10ec057e9ae26b07d0280b7f4341da5d1b1eae06c7d,
                      0x9b2f2f6d9c5628a7844163d015be86344082aa88d95e2f9d),
        0xfffffffffffffffffffffffe26f2fc170f69466a74defd8d,
        1,
        24,
        24
    ),
    "prime256v1": EllipticCurve(
        0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff,
        0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc,
        0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b,
        EllipticPoint(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
                      0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5),
        0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551,
        1,
        32,
        16
    )
}
