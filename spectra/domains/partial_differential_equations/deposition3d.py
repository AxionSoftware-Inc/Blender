from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite
from typing import Literal

from spectra.core.types import Vec3
from spectra.domains.partial_differential_equations.domain3d import UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


DepositionScheme3D = Literal["nearest", "cloud_in_cell"]
OutsideMode3D = Literal["error", "clamp"]


@dataclass(frozen=True, slots=True)
class PointSource3D:
    position: Vec3
    strength: float

    def __post_init__(self) -> None:
        if not isfinite(float(self.strength)):
            raise ValueError("point source strength must be finite")


def _axis_location(value, axis, outside: OutsideMode3D) -> tuple[int, float]:
    sample = float(value)
    if outside == "error" and not (axis.start <= sample <= axis.end):
        raise ValueError("point source lies outside deposition grid")
    if outside == "clamp":
        sample = min(max(sample, axis.start), axis.end)
    elif outside != "error":
        raise ValueError(f"unknown deposition outside mode: {outside}")
    coordinate = (sample - axis.start) / axis.spacing
    lower = min(max(int(floor(coordinate)), 0), axis.count - 2)
    fraction = min(max(coordinate - lower, 0.0), 1.0)
    return lower, fraction


def deposit_point_weights_3d(
    grid: UniformGrid3D,
    sources: tuple[PointSource3D, ...],
    *,
    scheme: DepositionScheme3D = "cloud_in_cell",
    outside: OutsideMode3D = "error",
) -> tuple[float, ...]:
    """Deposit integrated point strengths onto grid nodes.

    The returned nodal weights preserve total source strength exactly (up to
    floating-point rounding). They are integrated weights, not volume density.
    """

    if scheme not in {"nearest", "cloud_in_cell"}:
        raise ValueError(f"unknown 3D deposition scheme: {scheme}")
    values = [0.0 for _ in range(grid.count)]

    for source in sources:
        x, tx = _axis_location(source.position.x, grid.x, outside)
        y, ty = _axis_location(source.position.y, grid.y, outside)
        z, tz = _axis_location(source.position.z, grid.z, outside)

        if scheme == "nearest":
            xi = x + int(tx >= 0.5)
            yi = y + int(ty >= 0.5)
            zi = z + int(tz >= 0.5)
            values[grid.flat_index(xi, yi, zi)] += float(source.strength)
            continue

        for dz, wz in ((0, 1.0 - tz), (1, tz)):
            for dy, wy in ((0, 1.0 - ty), (1, ty)):
                for dx, wx in ((0, 1.0 - tx), (1, tx)):
                    weight = wx * wy * wz
                    values[grid.flat_index(x + dx, y + dy, z + dz)] += (
                        float(source.strength) * weight
                    )

    return tuple(values)


def deposit_point_density_3d(
    grid: UniformGrid3D,
    sources: tuple[PointSource3D, ...],
    *,
    scheme: DepositionScheme3D = "cloud_in_cell",
    outside: OutsideMode3D = "error",
) -> tuple[float, ...]:
    """Deposit point strengths as nodal density per coordinate-volume."""

    weights = deposit_point_weights_3d(grid, sources, scheme=scheme, outside=outside)
    cell_volume = grid.x.spacing * grid.y.spacing * grid.z.spacing
    return tuple(value / cell_volume for value in weights)


class SourceDeposition3DDomain:
    name = "partial_differential_equations.deposition3d"
    version = "1"
    dependencies = (DomainDependency("pde.uniform_grid3d"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("pde.point_source3d", PointSource3D)
        registry.provide("pde.point_source3d", PointSource3D)
        registry.provide("pde.deposit_point_weights_3d", deposit_point_weights_3d)
        registry.provide("pde.deposit_point_density_3d", deposit_point_density_3d)
