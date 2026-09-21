"""2D vector, matching Kaplay's vec2()."""
from __future__ import annotations
import math


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return f"vec2({self.x:g}, {self.y:g})"

    def __iter__(self):
        yield self.x
        yield self.y

    def __eq__(self, other):
        if isinstance(other, Vec2):
            return self.x == other.x and self.y == other.y
        return NotImplemented

    def __add__(self, other):
        other = _coerce(other)
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        other = _coerce(other)
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        if isinstance(scalar, Vec2):
            return Vec2(self.x * scalar.x, self.y * scalar.y)
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar):
        if isinstance(scalar, Vec2):
            return Vec2(self.x / scalar.x, self.y / scalar.y)
        return Vec2(self.x / scalar, self.y / scalar)

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    # Kaplay-style methods (camelCase, called as .sub()/.add()/.scale() too)
    def add(self, other):
        return self + other

    def sub(self, other):
        return self - other

    def scale(self, s):
        return self * s

    def dot(self, other):
        other = _coerce(other)
        return self.x * other.x + self.y * other.y

    def dist(self, other):
        other = _coerce(other)
        return math.hypot(self.x - other.x, self.y - other.y)

    def len(self):
        return math.hypot(self.x, self.y)

    def unit(self):
        length = self.len()
        if length == 0:
            return Vec2(0, 0)
        return Vec2(self.x / length, self.y / length)

    def angle(self, other=None):
        if other is None:
            return math.degrees(math.atan2(self.y, self.x))
        other = _coerce(other)
        return math.degrees(math.atan2(other.y - self.y, other.x - self.x))

    def lerp(self, other, t):
        other = _coerce(other)
        return Vec2(self.x + (other.x - self.x) * t, self.y + (other.y - self.y) * t)

    def clone(self):
        return Vec2(self.x, self.y)

    def to_tuple(self):
        return (self.x, self.y)


def _coerce(v):
    if isinstance(v, Vec2):
        return v
    if isinstance(v, (tuple, list)) and len(v) == 2:
        return Vec2(v[0], v[1])
    if isinstance(v, (int, float)):
        return Vec2(v, v)
    raise TypeError(f"expected vec2-like, got {v!r}")


_UNSET = object()


def vec2(x=0.0, y=_UNSET):
    """kaplay's vec2(x, y). Also accepts vec2(vec2), vec2((x, y)), and vec2(n) for (n, n)."""
    if isinstance(x, Vec2):
        return Vec2(x.x, x.y)
    if isinstance(x, (tuple, list)) and len(x) == 2:
        return Vec2(x[0], x[1])
    if y is _UNSET:
        # single number: vec2(n) -> (n, n)
        return Vec2(x, x)
    return Vec2(x, y)
