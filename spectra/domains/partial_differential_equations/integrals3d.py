from __future__ import annotations

from collections.abc import Iterable
import math

from spectra.core.types import Vec3
from spectra.domains.partial_differential_equations.domain3d import UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


def _axis_weight(index: int, count: int) -> float:
    return 0.5 if index in {0, count - 1} else 1.0


def integrate_scalar_grid_3d(
    values: Iterable[float],
    grid: UniformGrid3D,
) -> float:
    """Tensor-product trapezoidal integral over a rectangular UniformGrid3D."""

    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("3D integral scalar sample count must match grid")
    if not all(math.isfinite(value) for value in state):
        raise ValueError("3D integral scalar samples must be finite")

    total = 0.0
    for z_index in range(grid.z.count):
        wz = _axis_weight(z_index, grid.z.count)
        for y_index in range(grid.y.count):
            wy = _axis_weight(y_index, grid.y.count)
            for x_index in range(grid.x.count):
                wx = _axis_weight(x_index, grid.x.count)
                total += wx * wy * wz * state[grid.flat_index(x_index, y_index, z_index)]
    return total * grid.x.spacing * grid.y.spacing * grid.z.spacing


def integrate_vector_magnitude_squared_grid_3d(
    values: Iterable[Vec3],
    grid: UniformGrid3D,
) -> float:
    vectors = tuple(values)
    if len(vectors) != grid.count:
        raise ValueError("3D vector integral sample count must match grid")
    if any(not isinstance(vector, Vec3) for vector in vectors):
        raise TypeError("3D vector integral samples must be Vec3")
    return integrate_scalar_grid_3d(
        tuple(vector.dot(vector) for vector in vectors),
        grid,
    )


def scalar_l2_norm_grid_3d(
    values: Iterable[float],
    grid: UniformGrid3D,
) -> float:
    state = tuple(float(value) for value in values)
    squared = integrate_scalar_grid_3d(tuple(value * value for value in state), grid)
    return math.sqrt(max(squared, 0.0))


class GridIntegrals3DDomain:
    name = "partial_differential_equations.integrals3d"
    version = "1"
    dependencies = (DomainDependency("pde.uniform_grid3d"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.integrate_scalar_grid_3d", integrate_scalar_grid_3d)
        registry.provide(
            "pde.integrate_vector_magnitude_squared_grid_3d",
            integrate_vector_magnitude_squared_grid_3d,
        )
        registry.provide("pde.scalar_l2_norm_grid_3d", scalar_l2_norm_grid_3d)
