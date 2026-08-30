from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain3d import (
    ScalarPDESolution3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


ScalarState3D = tuple[float, ...]
AccelerationRhs3D = Callable[
    [float, UniformGrid3D, ScalarState3D, ScalarState3D],
    ScalarState3D,
]


@dataclass(frozen=True, slots=True)
class SecondOrderScalarPDEProblem3D:
    grid: UniformGrid3D
    initial_values: ScalarState3D
    initial_velocity: ScalarState3D
    acceleration_rhs: AccelerationRhs3D
    initial_time: float = 0.0
    name: str = "second_order_scalar_pde_3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("second-order 3D PDE initial values must match grid")
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("second-order 3D PDE initial velocity must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("second-order 3D PDE initial values must be finite")
        if not all(math.isfinite(float(value)) for value in self.initial_velocity):
            raise ValueError("second-order 3D PDE initial velocity must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("second-order 3D PDE initial time must be finite")
        if not self.name:
            raise ValueError("second-order 3D PDE name cannot be empty")


@dataclass(frozen=True, slots=True)
class SecondOrderScalarPDESolution3D:
    grid: UniformGrid3D
    times: tuple[float, ...]
    values: tuple[ScalarState3D, ...]
    velocities: tuple[ScalarState3D, ...]
    name: str = "second_order_scalar_pde_3d"

    def __post_init__(self) -> None:
        if not self.times:
            raise ValueError("second-order 3D PDE solution cannot be empty")
        if not (len(self.times) == len(self.values) == len(self.velocities)):
            raise ValueError("second-order 3D PDE solution array length mismatch")
        if any(len(state) != self.grid.count for state in self.values):
            raise ValueError("second-order 3D PDE value state length must match grid")
        if any(len(state) != self.grid.count for state in self.velocities):
            raise ValueError("second-order 3D PDE velocity state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("second-order 3D PDE times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]

    def value_solution(self) -> ScalarPDESolution3D:
        return ScalarPDESolution3D(
            grid=self.grid,
            times=self.times,
            states=self.values,
            name=self.name,
        )


class SecondOrderPDE3DDomain:
    """Second-order 3D temporal dynamics lowered to the generic ODE contract."""

    name = "partial_differential_equations.second_order3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_second_order(
            problem: SecondOrderScalarPDEProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> SecondOrderScalarPDESolution3D:
            count = problem.grid.count
            initial_state = tuple(problem.initial_values) + tuple(problem.initial_velocity)

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != count * 2:
                    raise ValueError("second-order 3D PDE ODE state has invalid dimension")
                values = tuple(float(value) for value in state[:count])
                velocities = tuple(float(value) for value in state[count:])
                acceleration = tuple(
                    float(value)
                    for value in problem.acceleration_rhs(
                        time,
                        problem.grid,
                        values,
                        velocities,
                    )
                )
                if len(acceleration) != count:
                    raise ValueError("second-order 3D PDE acceleration returned wrong dimension")
                if not all(math.isfinite(value) for value in acceleration):
                    raise ValueError("second-order 3D PDE acceleration returned non-finite values")
                return velocities + acceleration

            ode_solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=initial_state,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return SecondOrderScalarPDESolution3D(
                grid=problem.grid,
                times=ode_solution.times,
                values=tuple(tuple(state[:count]) for state in ode_solution.states),
                velocities=tuple(tuple(state[count:]) for state in ode_solution.states),
                name=problem.name,
            )

        registry.register_semantic_type(
            "pde.second_order_problem3d",
            SecondOrderScalarPDEProblem3D,
        )
        registry.register_semantic_type(
            "pde.second_order_solution3d",
            SecondOrderScalarPDESolution3D,
        )
        registry.provide("pde.second_order_problem3d", SecondOrderScalarPDEProblem3D)
        registry.provide("pde.second_order_solution3d", SecondOrderScalarPDESolution3D)
        registry.provide("pde.solve_second_order_3d", solve_second_order)
