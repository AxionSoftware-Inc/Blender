from __future__ import annotations

from collections.abc import Iterable
from math import floor
from typing import Literal

from spectra.core.types import Vec3
from spectra.core.units import Unit
from spectra.domains.mathematics.fields import ScalarField3D, VectorField3D
from spectra.domains.partial_differential_equations.domain3d import UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


OutsideMode3D = Literal["error", "clamp"]


def _axis_coordinate(value, start, end, spacing, count, outside):
    sample = float(value)
    if outside == "error" and not (start <= sample <= end):
        raise ValueError("3D sample position lies outside grid domain")
    if outside == "clamp":
        sample = min(max(sample, start), end)
    elif outside != "error":
        raise ValueError(f"unknown 3D sampled-field outside mode: {outside}")
    coordinate = (sample - start) / spacing
    lower = min(max(int(floor(coordinate)), 0), count - 2)
    fraction = min(max(coordinate - lower, 0.0), 1.0)
    return lower, fraction


def _cell(grid: UniformGrid3D, position: Vec3, outside: OutsideMode3D):
    x, tx = _axis_coordinate(
        position.x, grid.x.start, grid.x.end, grid.x.spacing, grid.x.count, outside
    )
    y, ty = _axis_coordinate(
        position.y, grid.y.start, grid.y.end, grid.y.spacing, grid.y.count, outside
    )
    z, tz = _axis_coordinate(
        position.z, grid.z.start, grid.z.end, grid.z.spacing, grid.z.count, outside
    )
    return x, y, z, tx, ty, tz


def _lerp(left, right, fraction):
    return left * (1.0 - fraction) + right * fraction


def scalar_field_from_grid_3d(
    grid: UniformGrid3D,
    values: Iterable[float],
    *,
    name: str = "sampled_scalar_field3d",
    output_unit: Unit | None = None,
    outside: OutsideMode3D = "error",
) -> ScalarField3D:
    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("sampled 3D scalar value count must match grid")

    def evaluate(position: Vec3) -> float:
        x, y, z, tx, ty, tz = _cell(grid, position, outside)
        samples = [
            state[grid.flat_index(x + dx, y + dy, z + dz)]
            for dz in (0, 1)
            for dy in (0, 1)
            for dx in (0, 1)
        ]
        z0y0 = _lerp(samples[0], samples[1], tx)
        z0y1 = _lerp(samples[2], samples[3], tx)
        z1y0 = _lerp(samples[4], samples[5], tx)
        z1y1 = _lerp(samples[6], samples[7], tx)
        z0 = _lerp(z0y0, z0y1, ty)
        z1 = _lerp(z1y0, z1y1, ty)
        return float(_lerp(z0, z1, tz))

    return ScalarField3D(evaluator=evaluate, name=name, output_unit=output_unit)


def vector_field_from_grid_3d(
    grid: UniformGrid3D,
    values: Iterable[Vec3],
    *,
    name: str = "sampled_vector_field3d",
    output_unit: Unit | None = None,
    outside: OutsideMode3D = "error",
) -> VectorField3D:
    state = tuple(values)
    if len(state) != grid.count:
        raise ValueError("sampled 3D vector value count must match grid")
    if any(not isinstance(value, Vec3) for value in state):
        raise TypeError("sampled 3D vector values must be Vec3")

    def evaluate(position: Vec3) -> Vec3:
        x, y, z, tx, ty, tz = _cell(grid, position, outside)
        samples = [
            state[grid.flat_index(x + dx, y + dy, z + dz)]
            for dz in (0, 1)
            for dy in (0, 1)
            for dx in (0, 1)
        ]
        z0y0 = _lerp(samples[0], samples[1], tx)
        z0y1 = _lerp(samples[2], samples[3], tx)
        z1y0 = _lerp(samples[4], samples[5], tx)
        z1y1 = _lerp(samples[6], samples[7], tx)
        z0 = _lerp(z0y0, z0y1, ty)
        z1 = _lerp(z1y0, z1y1, ty)
        return _lerp(z0, z1, tz)

    return VectorField3D(evaluator=evaluate, name=name, output_unit=output_unit)


class PDEFieldAdapters3DDomain:
    name = "partial_differential_equations.field_adapters3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.scalar_field_from_grid_3d", scalar_field_from_grid_3d)
        registry.provide("pde.vector_field_from_grid_3d", vector_field_from_grid_3d)
