from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float
    y: float
    z: float


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
