from __future__ import annotations

from collections.abc import Iterable
import math

from spectra.core.types import Vec2
from spectra.domains.partial_differential_equations.domain2d import UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


def _axis_weight(index: int, count: int) -> float:
    return 0.5 if index in {0, count - 1} else 1.0


def integrate_scalar_grid_2d(
    values: Iterable[float],
    grid: UniformGrid2D,
) -> float:
    """Tensor-product trapezoidal integral over a rectangular UniformGrid2D."""

    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("2D integral scalar sample count must match grid")
    if not all(math.isfinite(value) for value in state):
        raise ValueError("2D integral scalar samples must be finite")

    total = 0.0
    for y_index in range(grid.y.count):
        wy = _axis_weight(y_index, grid.y.count)
        for x_index in range(grid.x.count):
            wx = _axis_weight(x_index, grid.x.count)
            total += wx * wy * state[grid.flat_index(x_index, y_index)]
    return total * grid.x.spacing * grid.y.spacing


def integrate_vector_magnitude_squared_grid_2d(
    values: Iterable[Vec2],
    grid: UniformGrid2D,
) -> float:
    vectors = tuple(values)
    if len(vectors) != grid.count:
        raise ValueError("2D vector integral sample count must match grid")
    if any(not isinstance(vector, Vec2) for vector in vectors):
        raise TypeError("2D vector integral samples must be Vec2")
    return integrate_scalar_grid_2d(
        tuple(vector.dot(vector) for vector in vectors),
        grid,
    )


def scalar_l2_norm_grid_2d(
    values: Iterable[float],
    grid: UniformGrid2D,
) -> float:
    state = tuple(float(value) for value in values)
    squared = integrate_scalar_grid_2d(tuple(value * value for value in state), grid)
    return math.sqrt(max(squared, 0.0))


class GridIntegrals2DDomain:
    name = "partial_differential_equations.integrals2d"
    version = "1"
    dependencies = (DomainDependency("pde.uniform_grid2d"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.integrate_scalar_grid_2d", integrate_scalar_grid_2d)
        registry.provide(
            "pde.integrate_vector_magnitude_squared_grid_2d",
            integrate_vector_magnitude_squared_grid_2d,
        )
        registry.provide("pde.scalar_l2_norm_grid_2d", scalar_l2_norm_grid_2d)
