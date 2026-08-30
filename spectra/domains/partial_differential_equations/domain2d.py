from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math
from typing import Literal

from spectra.domains.partial_differential_equations.domain import UniformGrid1D
from spectra.domains.registry import DomainDependency, DomainRegistry


BoundaryMode2D = Literal["fixed", "periodic", "zero_gradient"]
ScalarState2D = tuple[float, ...]
ScalarPDERhs2D = Callable[[float, "UniformGrid2D", ScalarState2D], ScalarState2D]


@dataclass(frozen=True, slots=True)
class UniformGrid2D:
    x: UniformGrid1D
    y: UniformGrid1D

    @property
    def count(self) -> int:
        return self.x.count * self.y.count

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.count, self.x.count)

    def flat_index(self, x_index: int, y_index: int) -> int:
        if not 0 <= x_index < self.x.count:
            raise IndexError("2D PDE x index out of range")
        if not 0 <= y_index < self.y.count:
            raise IndexError("2D PDE y index out of range")
        return y_index * self.x.count + x_index

    @property
    def coordinates(self) -> tuple[tuple[float, float], ...]:
        return tuple(
            (x, y)
            for y in self.y.coordinates
            for x in self.x.coordinates
        )


@dataclass(frozen=True, slots=True)
class ScalarPDEProblem2D:
    grid: UniformGrid2D
    initial_values: ScalarState2D
    rhs: ScalarPDERhs2D
    initial_time: float = 0.0
    name: str = "scalar_pde_2d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("2D PDE initial_values length must match grid point count")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("2D PDE initial values must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("2D PDE initial_time must be finite")
        if not self.name:
            raise ValueError("2D PDE problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ScalarPDESolution2D:
    grid: UniformGrid2D
    times: tuple[float, ...]
    states: tuple[ScalarState2D, ...]
    name: str = "scalar_pde_2d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("2D PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("2D PDE solution times/states length mismatch")
        if any(len(state) != self.grid.count for state in self.states):
            raise ValueError("2D PDE solution state length must match grid point count")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("2D PDE solution times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]


def _neighbour_index(index: int, count: int, direction: int, boundary: BoundaryMode2D) -> int | None:
    candidate = index + direction
    if 0 <= candidate < count:
        return candidate
    if boundary == "fixed":
        return None
    if boundary == "periodic":
        if index == 0 and direction < 0:
            return count - 2
        if index == count - 1 and direction > 0:
            return 1
    if boundary == "zero_gradient":
        if index == 0 and direction < 0:
            return 1
        if index == count - 1 and direction > 0:
            return count - 2
    raise ValueError(f"unknown 2D boundary mode: {boundary}")


def laplacian_2d(
    values: Iterable[float],
    grid: UniformGrid2D,
    *,
    boundary: BoundaryMode2D = "fixed",
) -> ScalarState2D:
    """Five-point Laplacian on a rectangular uniform grid."""

    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 2D boundary mode: {boundary}")
    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("2D field values length must match grid point count")

    inv_dx2 = 1.0 / (grid.x.spacing * grid.x.spacing)
    inv_dy2 = 1.0 / (grid.y.spacing * grid.y.spacing)
    result = [0.0] * grid.count

    for y_index in range(grid.y.count):
        for x_index in range(grid.x.count):
            center_index = grid.flat_index(x_index, y_index)
            if boundary == "fixed" and (
                x_index in {0, grid.x.count - 1}
                or y_index in {0, grid.y.count - 1}
            ):
                result[center_index] = 0.0
                continue

            left_x = _neighbour_index(x_index, grid.x.count, -1, boundary)
            right_x = _neighbour_index(x_index, grid.x.count, 1, boundary)
            lower_y = _neighbour_index(y_index, grid.y.count, -1, boundary)
            upper_y = _neighbour_index(y_index, grid.y.count, 1, boundary)
            if None in {left_x, right_x, lower_y, upper_y}:
                result[center_index] = 0.0
                continue

            center = state[center_index]
            d2x = (
                state[grid.flat_index(int(left_x), y_index)]
                - 2.0 * center
                + state[grid.flat_index(int(right_x), y_index)]
            ) * inv_dx2
            d2y = (
                state[grid.flat_index(x_index, int(lower_y))]
                - 2.0 * center
                + state[grid.flat_index(x_index, int(upper_y))]
            ) * inv_dy2
            result[center_index] = d2x + d2y

    return tuple(result)


class PartialDifferentialEquations2DDomain:
    """Two-dimensional scalar PDE layer reusing the generic ODE integrator."""

    name = "partial_differential_equations.2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid1d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization2d import (
            compile_scalar_pde_solution_2d_scene,
        )

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_method_of_lines_2d(
            problem: ScalarPDEProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> ScalarPDESolution2D:
            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                values = tuple(float(value) for value in state)
                result = tuple(float(value) for value in problem.rhs(time, problem.grid, values))
                if len(result) != problem.grid.count:
                    raise ValueError("2D PDE rhs returned wrong state dimension")
                if not all(math.isfinite(value) for value in result):
                    raise ValueError("2D PDE rhs returned non-finite derivative")
                return result

            ode_solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=tuple(float(value) for value in problem.initial_values),
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return ScalarPDESolution2D(
                grid=problem.grid,
                times=ode_solution.times,
                states=tuple(tuple(float(value) for value in state) for state in ode_solution.states),
                name=problem.name,
            )

        registry.register_semantic_type("pde.uniform_grid2d", UniformGrid2D)
        registry.register_semantic_type("pde.scalar_problem2d", ScalarPDEProblem2D)
        registry.register_semantic_type("pde.scalar_solution2d", ScalarPDESolution2D)
        registry.provide("pde.uniform_grid2d", UniformGrid2D)
        registry.provide("pde.laplacian_2d", laplacian_2d)
        registry.provide("pde.solve_method_of_lines_2d", solve_method_of_lines_2d)
        registry.register_visualization(ScalarPDESolution2D, compile_scalar_pde_solution_2d_scene)
