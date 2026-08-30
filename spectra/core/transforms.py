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

    @staticmethod
    def from_basis(x_axis: Vec3, y_axis: Vec3, z_axis: Vec3) -> "Quaternion":
        """Create rotation from orthonormal world-space local axes."""
        x_axis = x_axis.normalized()
        y_axis = y_axis.normalized()
        z_axis = z_axis.normalized()

        m00, m01, m02 = x_axis.x, y_axis.x, z_axis.x
        m10, m11, m12 = x_axis.y, y_axis.y, z_axis.y
        m20, m21, m22 = x_axis.z, y_axis.z, z_axis.z
        trace = m00 + m11 + m22

        if trace > 0.0:
            s = math.sqrt(trace + 1.0) * 2.0
            return Quaternion(
                0.25 * s,
                (m21 - m12) / s,
                (m02 - m20) / s,
                (m10 - m01) / s,
            )
        if m00 > m11 and m00 > m22:
            s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
            return Quaternion(
                (m21 - m12) / s,
                0.25 * s,
                (m01 + m10) / s,
                (m02 + m20) / s,
            )
        if m11 > m22:
            s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
            return Quaternion(
                (m02 - m20) / s,
                (m01 + m10) / s,
                0.25 * s,
                (m12 + m21) / s,
            )
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        return Quaternion(
            (m10 - m01) / s,
            (m02 + m20) / s,
            (m12 + m21) / s,
            0.25 * s,
        )

    def dot(self, other: "Quaternion") -> float:
        return self.w * other.w + self.x * other.x + self.y * other.y + self.z * other.z

    def rotate(self, vector: Vec3) -> Vec3:
        """Rotate a vector by this unit quaternion."""
        axis = Vec3(self.x, self.y, self.z)
        axis_dot = axis.dot(vector)
        axis_norm_sq = axis.dot(axis)
        return (
            axis * (2.0 * axis_dot)
            + vector * (self.w * self.w - axis_norm_sq)
            + axis.cross(vector) * (2.0 * self.w)
        )


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

    @staticmethod
    def look_at(
        eye: Vec3,
        target: Vec3,
        *,
        up: Vec3 = Vec3(0.0, 1.0, 0.0),
    ) -> "Transform3D":
        """Create a camera-style transform with local -Z looking at target."""
        forward = (target - eye).normalized()
        right = forward.cross(up)
        if right.magnitude == 0.0:
            raise ValueError("look_at up vector cannot be parallel to viewing direction")
        right = right.normalized()
        corrected_up = right.cross(forward).normalized()
        local_z = forward * -1.0
        return Transform3D(
            translation=eye,
            rotation=Quaternion.from_basis(right, corrected_up, local_z),
        )
