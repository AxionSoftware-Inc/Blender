from __future__ import annotations

from collections.abc import Iterable
from math import floor, isfinite
from typing import Literal

from spectra.core.types import Vec3
from spectra.core.units import Unit
from spectra.domains.mathematics.fields import (
    ScalarField3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)
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


def _sample_scalar(
    grid: UniformGrid3D,
    state: tuple[float, ...],
    position: Vec3,
    outside: OutsideMode3D,
) -> float:
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


def _sample_vector(
    grid: UniformGrid3D,
    state: tuple[Vec3, ...],
    position: Vec3,
    outside: OutsideMode3D,
) -> Vec3:
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


def _validate_times(times: Iterable[float]) -> tuple[float, ...]:
    result = tuple(float(value) for value in times)
    if not result:
        raise ValueError("sampled 3D time field requires at least one time")
    if not all(isfinite(value) for value in result):
        raise ValueError("sampled 3D field times must be finite")
    if any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError("sampled 3D field times must be strictly increasing")
    return result


def _time_bracket(
    times: tuple[float, ...],
    time: float,
    outside: OutsideMode3D,
) -> tuple[int, int, float]:
    sample = float(time)
    if not isfinite(sample):
        raise ValueError("3D sample time must be finite")
    if outside not in {"error", "clamp"}:
        raise ValueError(f"unknown 3D sampled-field outside mode: {outside}")
    if len(times) == 1:
        if outside == "error" and sample != times[0]:
            raise ValueError("3D sample time lies outside time-series domain")
        return 0, 0, 0.0
    if sample < times[0] or sample > times[-1]:
        if outside == "error":
            raise ValueError("3D sample time lies outside time-series domain")
        sample = min(max(sample, times[0]), times[-1])
    if sample <= times[0]:
        return 0, 0, 0.0
    if sample >= times[-1]:
        last = len(times) - 1
        return last, last, 0.0
    for left_index, (left, right) in enumerate(zip(times, times[1:])):
        if left <= sample <= right:
            return left_index, left_index + 1, (sample - left) / (right - left)
    raise RuntimeError("failed to bracket sampled 3D time")


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
    return ScalarField3D(
        evaluator=lambda position: _sample_scalar(grid, state, position, outside),
        name=name,
        output_unit=output_unit,
    )


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
    return VectorField3D(
        evaluator=lambda position: _sample_vector(grid, state, position, outside),
        name=name,
        output_unit=output_unit,
    )


def time_scalar_field_from_grid_3d(
    grid: UniformGrid3D,
    times: Iterable[float],
    states: Iterable[Iterable[float]],
    *,
    name: str = "sampled_time_scalar_field3d",
    output_unit: Unit | None = None,
    spatial_outside: OutsideMode3D = "error",
    temporal_outside: OutsideMode3D = "clamp",
) -> TimeDependentScalarField3D:
    time_values = _validate_times(times)
    state_values = tuple(tuple(float(value) for value in state) for state in states)
    if len(state_values) != len(time_values):
        raise ValueError("sampled 3D scalar time/state length mismatch")
    if any(len(state) != grid.count for state in state_values):
        raise ValueError("sampled 3D scalar state length must match grid")

    def evaluate(position: Vec3, time: float) -> float:
        left, right, fraction = _time_bracket(time_values, time, temporal_outside)
        left_value = _sample_scalar(grid, state_values[left], position, spatial_outside)
        if left == right:
            return left_value
        right_value = _sample_scalar(grid, state_values[right], position, spatial_outside)
        return left_value * (1.0 - fraction) + right_value * fraction

    return TimeDependentScalarField3D(evaluator=evaluate, name=name, output_unit=output_unit)


def time_vector_field_from_grid_3d(
    grid: UniformGrid3D,
    times: Iterable[float],
    states: Iterable[Iterable[Vec3]],
    *,
    name: str = "sampled_time_vector_field3d",
    output_unit: Unit | None = None,
    spatial_outside: OutsideMode3D = "error",
    temporal_outside: OutsideMode3D = "clamp",
) -> TimeDependentVectorField3D:
    time_values = _validate_times(times)
    state_values = tuple(tuple(state) for state in states)
    if len(state_values) != len(time_values):
        raise ValueError("sampled 3D vector time/state length mismatch")
    if any(len(state) != grid.count for state in state_values):
        raise ValueError("sampled 3D vector state length must match grid")
    if any(not isinstance(value, Vec3) for state in state_values for value in state):
        raise TypeError("sampled 3D vector states must contain Vec3")

    def evaluate(position: Vec3, time: float) -> Vec3:
        left, right, fraction = _time_bracket(time_values, time, temporal_outside)
        left_value = _sample_vector(grid, state_values[left], position, spatial_outside)
        if left == right:
            return left_value
        right_value = _sample_vector(grid, state_values[right], position, spatial_outside)
        return left_value * (1.0 - fraction) + right_value * fraction

    return TimeDependentVectorField3D(evaluator=evaluate, name=name, output_unit=output_unit)


class PDEFieldAdapters3DDomain:
    name = "partial_differential_equations.field_adapters3d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("mathematics.time_scalar_field3d"),
        DomainDependency("mathematics.time_vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.scalar_field_from_grid_3d", scalar_field_from_grid_3d)
        registry.provide("pde.vector_field_from_grid_3d", vector_field_from_grid_3d)
        registry.provide(
            "pde.time_scalar_field_from_grid_3d",
            time_scalar_field_from_grid_3d,
            version=2,
        )
        registry.provide(
            "pde.time_vector_field_from_grid_3d",
            time_vector_field_from_grid_3d,
            version=2,
        )
