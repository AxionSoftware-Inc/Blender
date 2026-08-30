from __future__ import annotations

from collections.abc import Iterable
from math import floor, isfinite
from typing import Literal

from spectra.core.types import Vec2
from spectra.core.units import Unit
from spectra.domains.mathematics.fields2d import (
    ScalarField2D,
    TimeDependentScalarField2D,
    TimeDependentVectorField2D,
    VectorField2D,
)
from spectra.domains.partial_differential_equations.domain2d import UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


OutsideMode = Literal["error", "clamp"]


def _axis_coordinate(
    value: float,
    start: float,
    end: float,
    spacing: float,
    count: int,
    outside: OutsideMode,
) -> tuple[int, float]:
    sample = float(value)
    if outside == "error" and not (start <= sample <= end):
        raise ValueError("sample position lies outside grid domain")
    if outside == "clamp":
        sample = min(max(sample, start), end)
    elif outside != "error":
        raise ValueError(f"unknown sampled-field outside mode: {outside}")

    coordinate = (sample - start) / spacing
    lower = min(max(int(floor(coordinate)), 0), count - 2)
    fraction = min(max(coordinate - lower, 0.0), 1.0)
    return lower, fraction


def _cell_weights(
    grid: UniformGrid2D,
    position: Vec2,
    outside: OutsideMode,
) -> tuple[int, int, float, float]:
    x_index, tx = _axis_coordinate(
        position.x,
        grid.x.start,
        grid.x.end,
        grid.x.spacing,
        grid.x.count,
        outside,
    )
    y_index, ty = _axis_coordinate(
        position.y,
        grid.y.start,
        grid.y.end,
        grid.y.spacing,
        grid.y.count,
        outside,
    )
    return x_index, y_index, tx, ty


def _sample_scalar(
    grid: UniformGrid2D,
    state: tuple[float, ...],
    position: Vec2,
    outside: OutsideMode,
) -> float:
    x, y, tx, ty = _cell_weights(grid, position, outside)
    v00 = state[grid.flat_index(x, y)]
    v10 = state[grid.flat_index(x + 1, y)]
    v01 = state[grid.flat_index(x, y + 1)]
    v11 = state[grid.flat_index(x + 1, y + 1)]
    lower = v00 * (1.0 - tx) + v10 * tx
    upper = v01 * (1.0 - tx) + v11 * tx
    return lower * (1.0 - ty) + upper * ty


def _sample_vector(
    grid: UniformGrid2D,
    state: tuple[Vec2, ...],
    position: Vec2,
    outside: OutsideMode,
) -> Vec2:
    x, y, tx, ty = _cell_weights(grid, position, outside)
    v00 = state[grid.flat_index(x, y)]
    v10 = state[grid.flat_index(x + 1, y)]
    v01 = state[grid.flat_index(x, y + 1)]
    v11 = state[grid.flat_index(x + 1, y + 1)]
    lower = v00 * (1.0 - tx) + v10 * tx
    upper = v01 * (1.0 - tx) + v11 * tx
    return lower * (1.0 - ty) + upper * ty


def _validate_times(times: Iterable[float]) -> tuple[float, ...]:
    result = tuple(float(value) for value in times)
    if not result:
        raise ValueError("sampled time field requires at least one time")
    if not all(isfinite(value) for value in result):
        raise ValueError("sampled time field times must be finite")
    if any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError("sampled time field times must be strictly increasing")
    return result


def _time_bracket(
    times: tuple[float, ...],
    time: float,
    outside: OutsideMode,
) -> tuple[int, int, float]:
    sample = float(time)
    if not isfinite(sample):
        raise ValueError("sample time must be finite")
    if len(times) == 1:
        if outside == "error" and sample != times[0]:
            raise ValueError("sample time lies outside time-series domain")
        if outside not in {"error", "clamp"}:
            raise ValueError(f"unknown sampled-field outside mode: {outside}")
        return 0, 0, 0.0

    if sample < times[0] or sample > times[-1]:
        if outside == "error":
            raise ValueError("sample time lies outside time-series domain")
        if outside != "clamp":
            raise ValueError(f"unknown sampled-field outside mode: {outside}")
        sample = min(max(sample, times[0]), times[-1])

    if sample <= times[0]:
        return 0, 0, 0.0
    if sample >= times[-1]:
        last = len(times) - 1
        return last, last, 0.0

    for left_index, (left, right) in enumerate(zip(times, times[1:])):
        if left <= sample <= right:
            fraction = (sample - left) / (right - left)
            return left_index, left_index + 1, fraction
    raise RuntimeError("failed to bracket sampled time")


def scalar_field_from_grid_2d(
    grid: UniformGrid2D,
    values: Iterable[float],
    *,
    name: str = "sampled_scalar_field2d",
    output_unit: Unit | None = None,
    outside: OutsideMode = "error",
) -> ScalarField2D:
    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("sampled scalar values length must match grid")

    return ScalarField2D(
        evaluator=lambda position: _sample_scalar(grid, state, position, outside),
        name=name,
        output_unit=output_unit,
    )


def vector_field_from_grid_2d(
    grid: UniformGrid2D,
    values: Iterable[Vec2],
    *,
    name: str = "sampled_vector_field2d",
    output_unit: Unit | None = None,
    outside: OutsideMode = "error",
) -> VectorField2D:
    state = tuple(values)
    if len(state) != grid.count:
        raise ValueError("sampled vector values length must match grid")
    if any(not isinstance(value, Vec2) for value in state):
        raise TypeError("sampled vector values must be Vec2")

    return VectorField2D(
        evaluator=lambda position: _sample_vector(grid, state, position, outside),
        name=name,
        output_unit=output_unit,
    )


def time_scalar_field_from_grid_2d(
    grid: UniformGrid2D,
    times: Iterable[float],
    states: Iterable[Iterable[float]],
    *,
    name: str = "sampled_time_scalar_field2d",
    output_unit: Unit | None = None,
    spatial_outside: OutsideMode = "error",
    temporal_outside: OutsideMode = "clamp",
) -> TimeDependentScalarField2D:
    time_values = _validate_times(times)
    state_values = tuple(tuple(float(value) for value in state) for state in states)
    if len(state_values) != len(time_values):
        raise ValueError("sampled scalar time/state length mismatch")
    if any(len(state) != grid.count for state in state_values):
        raise ValueError("sampled scalar state length must match grid")

    def evaluate(position: Vec2, time: float) -> float:
        left, right, fraction = _time_bracket(time_values, time, temporal_outside)
        left_value = _sample_scalar(grid, state_values[left], position, spatial_outside)
        if left == right:
            return left_value
        right_value = _sample_scalar(grid, state_values[right], position, spatial_outside)
        return left_value * (1.0 - fraction) + right_value * fraction

    return TimeDependentScalarField2D(
        evaluator=evaluate,
        name=name,
        output_unit=output_unit,
    )


def time_vector_field_from_grid_2d(
    grid: UniformGrid2D,
    times: Iterable[float],
    states: Iterable[Iterable[Vec2]],
    *,
    name: str = "sampled_time_vector_field2d",
    output_unit: Unit | None = None,
    spatial_outside: OutsideMode = "error",
    temporal_outside: OutsideMode = "clamp",
) -> TimeDependentVectorField2D:
    time_values = _validate_times(times)
    state_values = tuple(tuple(state) for state in states)
    if len(state_values) != len(time_values):
        raise ValueError("sampled vector time/state length mismatch")
    if any(len(state) != grid.count for state in state_values):
        raise ValueError("sampled vector state length must match grid")
    if any(not isinstance(value, Vec2) for state in state_values for value in state):
        raise TypeError("sampled vector states must contain Vec2")

    def evaluate(position: Vec2, time: float) -> Vec2:
        left, right, fraction = _time_bracket(time_values, time, temporal_outside)
        left_value = _sample_vector(grid, state_values[left], position, spatial_outside)
        if left == right:
            return left_value
        right_value = _sample_vector(grid, state_values[right], position, spatial_outside)
        return left_value * (1.0 - fraction) + right_value * fraction

    return TimeDependentVectorField2D(
        evaluator=evaluate,
        name=name,
        output_unit=output_unit,
    )


class PDEFieldAdapters2DDomain:
    name = "partial_differential_equations.field_adapters2d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("mathematics.scalar_field2d"),
        DomainDependency("mathematics.vector_field2d"),
        DomainDependency("mathematics.time_scalar_field2d"),
        DomainDependency("mathematics.time_vector_field2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.scalar_field_from_grid_2d", scalar_field_from_grid_2d)
        registry.provide("pde.vector_field_from_grid_2d", vector_field_from_grid_2d)
        registry.provide(
            "pde.time_scalar_field_from_grid_2d",
            time_scalar_field_from_grid_2d,
            version=2,
        )
        registry.provide(
            "pde.time_vector_field_from_grid_2d",
            time_vector_field_from_grid_2d,
            version=2,
        )
