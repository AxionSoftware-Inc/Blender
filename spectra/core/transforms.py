from __future__ import annotations

from dataclasses import dataclass
import math

from .types import Vec3


@dataclass(frozen=True, slots=True)
class Quaternion:
    """Renderer-independent unit quaternion (w, x, y, z)."""

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __post_init__(self) -> None:
        norm = math.sqrt(self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z)
        if norm == 0.0:
            raise ValueError("quaternion cannot be zero")
        if not math.isclose(norm, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            object.__setattr__(self, "w", self.w / norm)
            object.__setattr__(self, "x", self.x / norm)
            object.__setattr__(self, "y", self.y / norm)
            object.__setattr__(self, "z", self.z / norm)

    @staticmethod
    def identity() -> "Quaternion":
        return Quaternion()

    @staticmethod
    def from_axis_angle(axis: Vec3, angle_radians: float) -> "Quaternion":
        unit = axis.normalized()
        half = angle_radians * 0.5
        sine = math.sin(half)
        return Quaternion(math.cos(half), unit.x * sine, unit.y * sine, unit.z * sine)

    def dot(self, other: "Quaternion") -> float:
        return self.w * other.w + self.x * other.x + self.y * other.y + self.z * other.z


@dataclass(frozen=True, slots=True)
class Transform3D:
    """Generic transform shared by every visual primitive.

    Scientific geometry remains in scientific coordinates. This transform is a
    visual-space operation that renderer backends map to their native transform.
    """

    translation: Vec3 = Vec3(0.0, 0.0, 0.0)
    rotation: Quaternion = Quaternion()
    scale: Vec3 = Vec3(1.0, 1.0, 1.0)

    def __post_init__(self) -> None:
        if self.scale.x == 0.0 or self.scale.y == 0.0 or self.scale.z == 0.0:
            raise ValueError("transform scale components cannot be zero")
