from __future__ import annotations

from collections.abc import Iterable
from math import floor
from typing import Literal

from spectra.core.types import Vec2
from spectra.core.units import Unit
from spectra.domains.mathematics.fields2d import ScalarField2D, VectorField2D
from spectra.domains.partial_differential_equations.domain2d import UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


OutsideMode = Literal["error", "clamp"]


def _axis_coordinate(value: float, start: float, end: float, spacing: float, count: int, outside: OutsideMode) -> tuple[int, float]:
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


def _cell_weights(grid: UniformGrid2D, position: Vec2, outside: OutsideMode) -> tuple[int, int, float, float]:
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

    def evaluate(position: Vec2) -> float:
        x, y, tx, ty = _cell_weights(grid, position, outside)
        v00 = state[grid.flat_index(x, y)]
        v10 = state[grid.flat_index(x + 1, y)]
        v01 = state[grid.flat_index(x, y + 1)]
        v11 = state[grid.flat_index(x + 1, y + 1)]
        lower = v00 * (1.0 - tx) + v10 * tx
        upper = v01 * (1.0 - tx) + v11 * tx
        return lower * (1.0 - ty) + upper * ty

    return ScalarField2D(evaluator=evaluate, name=name, output_unit=output_unit)


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

    def evaluate(position: Vec2) -> Vec2:
        x, y, tx, ty = _cell_weights(grid, position, outside)
        v00 = state[grid.flat_index(x, y)]
        v10 = state[grid.flat_index(x + 1, y)]
        v01 = state[grid.flat_index(x, y + 1)]
        v11 = state[grid.flat_index(x + 1, y + 1)]
        lower = v00 * (1.0 - tx) + v10 * tx
        upper = v01 * (1.0 - tx) + v11 * tx
        return lower * (1.0 - ty) + upper * ty

    return VectorField2D(evaluator=evaluate, name=name, output_unit=output_unit)


class PDEFieldAdapters2DDomain:
    name = "partial_differential_equations.field_adapters2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("mathematics.scalar_field2d"),
        DomainDependency("mathematics.vector_field2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.scalar_field_from_grid_2d", scalar_field_from_grid_2d)
        registry.provide("pde.vector_field_from_grid_2d", vector_field_from_grid_2d)
