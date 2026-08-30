from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from spectra.core.primitives import Surface
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.mathematics.fields import AxisSample, ScalarField3D
from spectra.domains.registry import DomainDependency, DomainRegistry


SliceAxis3D = Literal["x", "y", "z"]


@dataclass(frozen=True, slots=True)
class ScalarFieldSliceSurface3D:
    """Sample a scalar field on a plane and displace along the plane normal."""

    field: ScalarField3D
    axis: SliceAxis3D
    coordinate: float
    u: AxisSample
    v: AxisSample
    height_scale: float = 1.0
    name: str = "scalar_field_slice3d"

    def __post_init__(self) -> None:
        if self.axis not in {"x", "y", "z"}:
            raise ValueError("scalar field slice axis must be x, y, or z")
        if not math.isfinite(self.coordinate):
            raise ValueError("scalar field slice coordinate must be finite")
        if self.u.count < 2 or self.v.count < 2:
            raise ValueError("scalar field slice requires at least 2x2 samples")
        if not math.isfinite(self.height_scale):
            raise ValueError("scalar field slice height_scale must be finite")
        if not self.name:
            raise ValueError("scalar field slice name cannot be empty")


def _triangles(u_count: int, v_count: int) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for v_index in range(v_count - 1):
        for u_index in range(u_count - 1):
            lower_left = v_index * u_count + u_index
            lower_right = lower_left + 1
            upper_left = lower_left + u_count
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))
    return tuple(triangles)


def _base_position(view: ScalarFieldSliceSurface3D, u: float, v: float) -> Vec3:
    if view.axis == "z":
        return Vec3(u, v, view.coordinate)
    if view.axis == "y":
        return Vec3(u, view.coordinate, v)
    return Vec3(view.coordinate, u, v)


def _displace(view: ScalarFieldSliceSurface3D, base: Vec3, value: float) -> Vec3:
    displacement = value * view.height_scale
    if view.axis == "z":
        return Vec3(base.x, base.y, base.z + displacement)
    if view.axis == "y":
        return Vec3(base.x, base.y + displacement, base.z)
    return Vec3(base.x + displacement, base.y, base.z)


def compile_scalar_field_slice_surface_scene(
    view: ScalarFieldSliceSurface3D,
    *,
    color: Color = Color(0.5, 0.72, 1.0, 0.92),
) -> Scene:
    vertices = []
    for v in view.v.values():
        for u in view.u.values():
            base = _base_position(view, u, v)
            vertices.append(_displace(view, base, view.field.evaluate(base)))
    return Scene(
        primitives=(
            Surface(
                id=view.name,
                vertices=tuple(vertices),
                triangles=_triangles(view.u.count, view.v.count),
                color=color,
            ),
        )
    )


class MathematicsFieldSlices3DDomain:
    name = "mathematics.field_slices3d"
    version = "1"
    dependencies = (DomainDependency("mathematics.scalar_field3d"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type(
            "mathematics.scalar_field_slice_surface3d",
            ScalarFieldSliceSurface3D,
        )
        registry.provide(
            "mathematics.scalar_field_slice_surface3d",
            ScalarFieldSliceSurface3D,
        )
        registry.register_visualization(
            ScalarFieldSliceSurface3D,
            compile_scalar_field_slice_surface_scene,
        )
