from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3


@dataclass(frozen=True, slots=True)
class CoordinateFrame3D:
    """Renderer-independent affine coordinate frame in scientific space."""

    origin: Vec3 = Vec3(0.0, 0.0, 0.0)
    basis_x: Vec3 = Vec3(1.0, 0.0, 0.0)
    basis_y: Vec3 = Vec3(0.0, 1.0, 0.0)
    basis_z: Vec3 = Vec3(0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        for axis in (self.basis_x, self.basis_y, self.basis_z):
            if axis.magnitude == 0.0:
                raise ValueError("coordinate basis vectors cannot be zero")
        determinant = self.basis_x.dot(self.basis_y.cross(self.basis_z))
        if math.isclose(determinant, 0.0, abs_tol=1e-12):
            raise ValueError("coordinate basis vectors must be linearly independent")

    @property
    def handedness(self) -> int:
        determinant = self.basis_x.dot(self.basis_y.cross(self.basis_z))
        return 1 if determinant > 0.0 else -1

    def point_to_parent(self, local: Vec3) -> Vec3:
        return (
            self.origin
            + self.basis_x * local.x
            + self.basis_y * local.y
            + self.basis_z * local.z
        )

    def vector_to_parent(self, local: Vec3) -> Vec3:
        return self.basis_x * local.x + self.basis_y * local.y + self.basis_z * local.z


WORLD_FRAME = CoordinateFrame3D()
