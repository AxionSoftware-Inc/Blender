from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.domains.partial_differential_equations.domain3d import UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


VectorState3D = tuple[Vec3, ...]
VectorAccelerationRhs3D = Callable[
    [float, UniformGrid3D, VectorState3D, VectorState3D],
    VectorState3D,
]


@dataclass(frozen=True, slots=True)
class SecondOrderVectorPDEProblem3D:
    grid: UniformGrid3D
    initial_values: VectorState3D
    initial_velocity: VectorState3D
    acceleration_rhs: VectorAccelerationRhs3D
    initial_time: float = 0.0
    name: str = "second_order_vector_pde_3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("second-order vector PDE initial values must match grid")
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("second-order vector PDE initial velocity must match grid")
        if any(not isinstance(value, Vec3) for value in self.initial_values):
            raise TypeError("second-order vector PDE initial values must be Vec3")
        if any(not isinstance(value, Vec3) for value in self.initial_velocity):
            raise TypeError("second-order vector PDE initial velocity must be Vec3")
        if not math.isfinite(self.initial_time):
            raise ValueError("second-order vector PDE initial time must be finite")
        if not self.name:
            raise ValueError("second-order vector PDE name cannot be empty")


@dataclass(frozen=True, slots=True)
class SecondOrderVectorPDESolution3D:
    grid: UniformGrid3D
    times: tuple[float, ...]
    values: tuple[VectorState3D, ...]
    velocities: tuple[VectorState3D, ...]
    name: str = "second_order_vector_pde_3d"

    def __post_init__(self) -> None:
        if not self.times:
            raise ValueError("second-order vector PDE solution cannot be empty")
        if not (len(self.times) == len(self.values) == len(self.velocities)):
            raise ValueError("second-order vector PDE history length mismatch")
        if any(len(state) != self.grid.count for state in self.values):
            raise ValueError("second-order vector PDE value state must match grid")
        if any(len(state) != self.grid.count for state in self.velocities):
            raise ValueError("second-order vector PDE velocity state must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("second-order vector PDE times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]


def _encode_vectors(values: VectorState3D) -> tuple[float, ...]:
    return tuple(component for value in values for component in (value.x, value.y, value.z))


def _decode_vectors(values: tuple[float, ...], count: int) -> VectorState3D:
    if len(values) != count * 3:
        raise ValueError("encoded vector PDE state has invalid dimension")
    return tuple(
        Vec3(values[index], values[index + 1], values[index + 2])
        for index in range(0, len(values), 3)
    )


class SecondOrderVectorPDE3DDomain:
    """Generic vector-valued u_tt = F(t,u,u_t) lowered to the selectable ODE role."""

    name = "partial_differential_equations.second_order_vector3d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)

        def solve_second_order_vector(
            problem: SecondOrderVectorPDEProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> SecondOrderVectorPDESolution3D:
            count = problem.grid.count
            encoded_values = _encode_vectors(problem.initial_values)
            encoded_velocity = _encode_vectors(problem.initial_velocity)
            initial_state = encoded_values + encoded_velocity
            vector_components = count * 3

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != vector_components * 2:
                    raise ValueError("second-order vector PDE ODE state has invalid dimension")
                values = _decode_vectors(tuple(state[:vector_components]), count)
                velocities = _decode_vectors(tuple(state[vector_components:]), count)
                acceleration = tuple(problem.acceleration_rhs(time, problem.grid, values, velocities))
                if len(acceleration) != count:
                    raise ValueError("second-order vector PDE acceleration returned wrong dimension")
                if any(not isinstance(value, Vec3) for value in acceleration):
                    raise TypeError("second-order vector PDE acceleration must contain Vec3")
                return _encode_vectors(velocities) + _encode_vectors(acceleration)

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
            return SecondOrderVectorPDESolution3D(
                grid=problem.grid,
                times=ode_solution.times,
                values=tuple(
                    _decode_vectors(tuple(state[:vector_components]), count)
                    for state in ode_solution.states
                ),
                velocities=tuple(
                    _decode_vectors(tuple(state[vector_components:]), count)
                    for state in ode_solution.states
                ),
                name=problem.name,
            )

        registry.register_semantic_type(
            "pde.second_order_vector_problem3d",
            SecondOrderVectorPDEProblem3D,
        )
        registry.register_semantic_type(
            "pde.second_order_vector_solution3d",
            SecondOrderVectorPDESolution3D,
        )
        registry.provide(
            "pde.second_order_vector_problem3d",
            SecondOrderVectorPDEProblem3D,
        )
        registry.provide(
            "pde.second_order_vector_solution3d",
            SecondOrderVectorPDESolution3D,
        )
        registry.provide(
            "pde.solve_second_order_vector_3d",
            solve_second_order_vector,
            version=2,
        )
