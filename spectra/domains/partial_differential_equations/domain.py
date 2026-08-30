from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math
from typing import Literal

from spectra.domains.registry import DomainDependency, DomainRegistry


BoundaryMode1D = Literal["fixed", "periodic", "zero_gradient"]
ScalarState1D = tuple[float, ...]
ScalarPDERhs1D = Callable[[float, "UniformGrid1D", ScalarState1D], ScalarState1D]


@dataclass(frozen=True, slots=True)
class UniformGrid1D:
    """Uniform one-dimensional spatial discretization for numerical PDE domains."""

    start: float
    end: float
    count: int

    def __post_init__(self) -> None:
        if not math.isfinite(self.start) or not math.isfinite(self.end):
            raise ValueError("PDE grid bounds must be finite")
        if self.end <= self.start:
            raise ValueError("PDE grid end must be greater than start")
        if self.count < 3:
            raise ValueError("PDE grid requires at least three points")

    @property
    def spacing(self) -> float:
        return (self.end - self.start) / (self.count - 1)

    @property
    def coordinates(self) -> tuple[float, ...]:
        step = self.spacing
        return tuple(self.start + step * index for index in range(self.count))


@dataclass(frozen=True, slots=True)
class ScalarPDEProblem1D:
    """Semi-discrete scalar PDE problem.

    `rhs(t, grid, values)` defines du/dt after spatial discretization. The PDE
    domain deliberately does not own a separate time integrator; it delegates
    temporal evolution to the versioned ODE capability.
    """

    grid: UniformGrid1D
    initial_values: ScalarState1D
    rhs: ScalarPDERhs1D
    initial_time: float = 0.0
    name: str = "scalar_pde_1d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("PDE initial_values length must match grid point count")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("PDE initial values must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("PDE initial_time must be finite")
        if not self.name:
            raise ValueError("PDE problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ScalarPDESolution1D:
    grid: UniformGrid1D
    times: tuple[float, ...]
    states: tuple[ScalarState1D, ...]
    name: str = "scalar_pde_1d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("PDE solution times/states length mismatch")
        if any(len(state) != self.grid.count for state in self.states):
            raise ValueError("PDE solution state length must match grid point count")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("PDE solution times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]


def second_derivative_1d(
    values: Iterable[float],
    grid: UniformGrid1D,
    *,
    boundary: BoundaryMode1D = "fixed",
) -> ScalarState1D:
    """Second spatial derivative on a uniform grid using central differences.

    `fixed` returns zero time-driving curvature at the endpoints, suitable for
    keeping Dirichlet endpoint values unchanged when used directly as a PDE RHS.
    `periodic` wraps endpoints. `zero_gradient` mirrors endpoint neighbours.
    """

    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("field values length must match grid point count")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 1D boundary mode: {boundary}")

    inv_h2 = 1.0 / (grid.spacing * grid.spacing)
    result = [0.0] * grid.count
    for index in range(1, grid.count - 1):
        result[index] = (
            state[index - 1] - 2.0 * state[index] + state[index + 1]
        ) * inv_h2

    if boundary == "periodic":
        result[0] = (state[-2] - 2.0 * state[0] + state[1]) * inv_h2
        result[-1] = (state[-2] - 2.0 * state[-1] + state[1]) * inv_h2
    elif boundary == "zero_gradient":
        result[0] = 2.0 * (state[1] - state[0]) * inv_h2
        result[-1] = 2.0 * (state[-2] - state[-1]) * inv_h2

    return tuple(result)


class PartialDifferentialEquationsDomain:
    """Spatial-discretization layer that reuses Spectra's ODE solver contract."""

    name = "partial_differential_equations"
    version = "1"
    dependencies = (
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization import (
            compile_scalar_pde_solution_scene,
        )

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_method_of_lines(
            problem: ScalarPDEProblem1D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> ScalarPDESolution1D:
            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                values = tuple(float(value) for value in state)
                result = tuple(float(value) for value in problem.rhs(time, problem.grid, values))
                if len(result) != problem.grid.count:
                    raise ValueError("PDE rhs returned wrong state dimension")
                if not all(math.isfinite(value) for value in result):
                    raise ValueError("PDE rhs returned non-finite derivative")
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
            return ScalarPDESolution1D(
                grid=problem.grid,
                times=ode_solution.times,
                states=tuple(tuple(float(value) for value in state) for state in ode_solution.states),
                name=problem.name,
            )

        registry.register_semantic_type("pde.uniform_grid1d", UniformGrid1D)
        registry.register_semantic_type("pde.scalar_problem1d", ScalarPDEProblem1D)
        registry.register_semantic_type("pde.scalar_solution1d", ScalarPDESolution1D)

        registry.provide("pde.uniform_grid1d", UniformGrid1D)
        registry.provide("pde.second_derivative_1d", second_derivative_1d)
        registry.provide("pde.solve_method_of_lines", solve_method_of_lines)
        registry.register_visualization(ScalarPDESolution1D, compile_scalar_pde_solution_scene)
