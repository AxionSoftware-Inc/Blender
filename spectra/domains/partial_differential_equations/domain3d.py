from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math
from typing import Literal

from spectra.domains.partial_differential_equations.domain import UniformGrid1D
from spectra.domains.registry import DomainDependency, DomainRegistry


BoundaryMode3D = Literal["fixed", "periodic", "zero_gradient"]
ScalarState3D = tuple[float, ...]
ScalarPDERhs3D = Callable[[float, "UniformGrid3D", ScalarState3D], ScalarState3D]


@dataclass(frozen=True, slots=True)
class UniformGrid3D:
    x: UniformGrid1D
    y: UniformGrid1D
    z: UniformGrid1D

    @property
    def count(self) -> int:
        return self.x.count * self.y.count * self.z.count

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.z.count, self.y.count, self.x.count)

    def flat_index(self, x_index: int, y_index: int, z_index: int) -> int:
        if not 0 <= x_index < self.x.count:
            raise IndexError("3D PDE x index out of range")
        if not 0 <= y_index < self.y.count:
            raise IndexError("3D PDE y index out of range")
        if not 0 <= z_index < self.z.count:
            raise IndexError("3D PDE z index out of range")
        return (z_index * self.y.count + y_index) * self.x.count + x_index

    @property
    def coordinates(self) -> tuple[tuple[float, float, float], ...]:
        return tuple(
            (x, y, z)
            for z in self.z.coordinates
            for y in self.y.coordinates
            for x in self.x.coordinates
        )


@dataclass(frozen=True, slots=True)
class ScalarPDEProblem3D:
    grid: UniformGrid3D
    initial_values: ScalarState3D
    rhs: ScalarPDERhs3D
    initial_time: float = 0.0
    name: str = "scalar_pde_3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("3D PDE initial_values length must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("3D PDE initial values must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D PDE initial_time must be finite")
        if not self.name:
            raise ValueError("3D PDE name cannot be empty")


@dataclass(frozen=True, slots=True)
class ScalarPDESolution3D:
    grid: UniformGrid3D
    times: tuple[float, ...]
    states: tuple[ScalarState3D, ...]
    name: str = "scalar_pde_3d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("3D PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("3D PDE solution times/states length mismatch")
        if any(len(state) != self.grid.count for state in self.states):
            raise ValueError("3D PDE state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("3D PDE solution times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]


def _neighbor(index: int, count: int, direction: int, boundary: BoundaryMode3D) -> int | None:
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
    raise ValueError(f"unknown 3D boundary mode: {boundary}")


def laplacian_3d(
    values: Iterable[float],
    grid: UniformGrid3D,
    *,
    boundary: BoundaryMode3D = "fixed",
) -> ScalarState3D:
    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("3D field values length must match grid")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 3D boundary mode: {boundary}")

    inv_dx2 = 1.0 / (grid.x.spacing * grid.x.spacing)
    inv_dy2 = 1.0 / (grid.y.spacing * grid.y.spacing)
    inv_dz2 = 1.0 / (grid.z.spacing * grid.z.spacing)
    result = [0.0] * grid.count

    for z_index in range(grid.z.count):
        for y_index in range(grid.y.count):
            for x_index in range(grid.x.count):
                center_index = grid.flat_index(x_index, y_index, z_index)
                if boundary == "fixed" and (
                    x_index in {0, grid.x.count - 1}
                    or y_index in {0, grid.y.count - 1}
                    or z_index in {0, grid.z.count - 1}
                ):
                    continue

                left = _neighbor(x_index, grid.x.count, -1, boundary)
                right = _neighbor(x_index, grid.x.count, 1, boundary)
                lower = _neighbor(y_index, grid.y.count, -1, boundary)
                upper = _neighbor(y_index, grid.y.count, 1, boundary)
                back = _neighbor(z_index, grid.z.count, -1, boundary)
                front = _neighbor(z_index, grid.z.count, 1, boundary)
                if None in {left, right, lower, upper, back, front}:
                    continue

                center = state[center_index]
                d2x = (
                    state[grid.flat_index(int(left), y_index, z_index)]
                    - 2.0 * center
                    + state[grid.flat_index(int(right), y_index, z_index)]
                ) * inv_dx2
                d2y = (
                    state[grid.flat_index(x_index, int(lower), z_index)]
                    - 2.0 * center
                    + state[grid.flat_index(x_index, int(upper), z_index)]
                ) * inv_dy2
                d2z = (
                    state[grid.flat_index(x_index, y_index, int(back))]
                    - 2.0 * center
                    + state[grid.flat_index(x_index, y_index, int(front))]
                ) * inv_dz2
                result[center_index] = d2x + d2y + d2z

    return tuple(result)


class PartialDifferentialEquations3DDomain:
    name = "partial_differential_equations.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid1d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_method_of_lines_3d(
            problem: ScalarPDEProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> ScalarPDESolution3D:
            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                values = tuple(float(value) for value in state)
                result = tuple(float(value) for value in problem.rhs(time, problem.grid, values))
                if len(result) != problem.grid.count:
                    raise ValueError("3D PDE rhs returned wrong state dimension")
                if not all(math.isfinite(value) for value in result):
                    raise ValueError("3D PDE rhs returned non-finite derivative")
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
            return ScalarPDESolution3D(
                grid=problem.grid,
                times=ode_solution.times,
                states=tuple(tuple(float(value) for value in state) for state in ode_solution.states),
                name=problem.name,
            )

        registry.register_semantic_type("pde.uniform_grid3d", UniformGrid3D)
        registry.register_semantic_type("pde.scalar_problem3d", ScalarPDEProblem3D)
        registry.register_semantic_type("pde.scalar_solution3d", ScalarPDESolution3D)
        registry.provide("pde.uniform_grid3d", UniformGrid3D)
        registry.provide("pde.laplacian_3d", laplacian_3d)
        registry.provide("pde.solve_method_of_lines_3d", solve_method_of_lines_3d)
