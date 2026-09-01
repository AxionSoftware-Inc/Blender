from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain3d import (
    ScalarPDESolution3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


ComponentState3D = tuple[float, ...]
CoupledState3D = tuple[ComponentState3D, ...]
CoupledPDERhs3D = Callable[[float, UniformGrid3D, CoupledState3D], CoupledState3D]


@dataclass(frozen=True, slots=True)
class CoupledScalarPDEProblem3D:
    grid: UniformGrid3D
    component_names: tuple[str, ...]
    initial_components: CoupledState3D
    rhs: CoupledPDERhs3D
    initial_time: float = 0.0
    name: str = "coupled_scalar_pde3d"

    def __post_init__(self) -> None:
        if not self.component_names:
            raise ValueError("coupled PDE requires at least one component")
        if len(self.component_names) != len(set(self.component_names)):
            raise ValueError("coupled PDE component names must be unique")
        if any(not name for name in self.component_names):
            raise ValueError("coupled PDE component names cannot be empty")
        if len(self.initial_components) != len(self.component_names):
            raise ValueError("coupled PDE initial component count mismatch")
        if any(len(component) != self.grid.count for component in self.initial_components):
            raise ValueError("coupled PDE component sample count must match grid")
        if any(
            not math.isfinite(float(value))
            for component in self.initial_components
            for value in component
        ):
            raise ValueError("coupled PDE initial samples must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("coupled PDE initial_time must be finite")
        if not self.name:
            raise ValueError("coupled PDE name cannot be empty")


@dataclass(frozen=True, slots=True)
class CoupledScalarPDESolution3D:
    grid: UniformGrid3D
    component_names: tuple[str, ...]
    times: tuple[float, ...]
    states: tuple[CoupledState3D, ...]
    name: str = "coupled_scalar_pde3d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("coupled PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("coupled PDE time/state history mismatch")
        if any(len(state) != len(self.component_names) for state in self.states):
            raise ValueError("coupled PDE state component count mismatch")
        if any(
            len(component) != self.grid.count
            for state in self.states
            for component in state
        ):
            raise ValueError("coupled PDE solution sample count must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("coupled PDE times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]

    def component_index(self, component: int | str) -> int:
        if isinstance(component, int):
            if not 0 <= component < len(self.component_names):
                raise IndexError("coupled PDE component index out of range")
            return component
        try:
            return self.component_names.index(component)
        except ValueError as exc:
            raise KeyError(f"unknown coupled PDE component: {component}") from exc

    def component_solution(self, component: int | str) -> ScalarPDESolution3D:
        index = self.component_index(component)
        component_name = self.component_names[index]
        return ScalarPDESolution3D(
            grid=self.grid,
            times=self.times,
            states=tuple(state[index] for state in self.states),
            name=f"{self.name}.{component_name}",
        )


def _encode(components: CoupledState3D) -> tuple[float, ...]:
    return tuple(float(value) for component in components for value in component)


def _decode(values: tuple[float, ...], component_count: int, grid_count: int) -> CoupledState3D:
    if len(values) != component_count * grid_count:
        raise ValueError("encoded coupled PDE state has invalid dimension")
    return tuple(
        tuple(float(value) for value in values[index * grid_count : (index + 1) * grid_count])
        for index in range(component_count)
    )


class CoupledScalarPDE3DDomain:
    """Generic N-component first-order PDE system lowered to the selectable ODE role."""

    name = "partial_differential_equations.coupled3d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)

        def solve(
            problem: CoupledScalarPDEProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> CoupledScalarPDESolution3D:
            component_count = len(problem.component_names)
            grid_count = problem.grid.count

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                components = _decode(state, component_count, grid_count)
                result = tuple(problem.rhs(time, problem.grid, components))
                if len(result) != component_count:
                    raise ValueError("coupled PDE rhs returned wrong component count")
                if any(len(component) != grid_count for component in result):
                    raise ValueError("coupled PDE rhs returned wrong sample count")
                if any(
                    not math.isfinite(float(value))
                    for component in result
                    for value in component
                ):
                    raise ValueError("coupled PDE rhs returned non-finite derivative")
                return _encode(result)

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=_encode(problem.initial_components),
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return CoupledScalarPDESolution3D(
                grid=problem.grid,
                component_names=problem.component_names,
                times=solution.times,
                states=tuple(
                    _decode(tuple(state), component_count, grid_count)
                    for state in solution.states
                ),
                name=problem.name,
            )

        registry.register_semantic_type(
            "pde.coupled_scalar_problem3d",
            CoupledScalarPDEProblem3D,
        )
        registry.register_semantic_type(
            "pde.coupled_scalar_solution3d",
            CoupledScalarPDESolution3D,
        )
        registry.provide("pde.coupled_scalar_problem3d", CoupledScalarPDEProblem3D)
        registry.provide("pde.coupled_scalar_solution3d", CoupledScalarPDESolution3D)
        registry.provide("pde.solve_coupled_scalar_3d", solve, version=2)
