from .point import EllipticPoint


class EllipticCurve:
    def __init__(
        self,
        P: int,
        A: int,
        B: int,
        G: EllipticPoint,
        N: int,
        H: int,
        size: int,
        pack_size: int,
    ):
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
        return (
            pow(point.y, 2) - pow(point.x, 3) - self._A * point.x - self._B
        ) % self._P == 0


CURVE = {
    "secp192k1": EllipticCurve(
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37,
        0,
        3,
        EllipticPoint(
            0xDB4FF10EC057E9AE26B07D0280B7F4341DA5D1B1EAE06C7D,
            0x9B2F2F6D9C5628A7844163D015BE86344082AA88D95E2F9D,
        ),
        0xFFFFFFFFFFFFFFFFFFFFFFFE26F2FC170F69466A74DEFD8D,
        1,
        24,
        24,
    ),
    "prime256v1": EllipticCurve(
        0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC,
        0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
        EllipticPoint(
            0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
            0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
        ),
        0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551,
        1,
        32,
        16,
    ),
}
