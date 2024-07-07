class EllipticPoint:
    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    def __eq__(self, other) -> bool:
        return isinstance(other, EllipticPoint) and self._x == other._x and self._y == other._y

    def __neg__(self):
        return EllipticPoint(-self._x, -self._y)

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def is_default(self) -> bool:
        return self._x == 0 and self._y == 0
