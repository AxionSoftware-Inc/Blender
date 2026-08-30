from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self) -> "Vec3":
        magnitude = self.magnitude
        if magnitude == 0.0:
            raise ValueError("zero vector cannot be normalized")
        return self * (1.0 / magnitude)


@dataclass(frozen=True, slots=True)
class Color:
    r: float
    g: float
    b: float
    a: float = 1.0

    def __post_init__(self) -> None:
        for value in (self.r, self.g, self.b, self.a):
            if not 0.0 <= value <= 1.0:
                raise ValueError("Color components must be within [0, 1]")
