from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.partial_differential_equations.transport3d import (
    AdvectionDiffusionProblem3D,
    AdvectionDiffusionSolution3D,
)
from spectra.domains.physics.fluid_kinematics3d import SteadyFlow3D, UnsteadyFlow3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PassiveScalarProblem3D:
    flow: UnsteadyFlow3D
    grid: UniformGrid3D
    initial_values: tuple[float, ...]
    diffusivity: float = 0.0
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "passive_scalar3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("3D passive scalar initial_values length must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("3D passive scalar initial values must be finite")
        if not math.isfinite(self.diffusivity) or self.diffusivity < 0.0:
            raise ValueError("3D passive scalar diffusivity must be finite and non-negative")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D passive scalar initial_time must be finite")
        if not self.name:
            raise ValueError("3D passive scalar name cannot be empty")

    @classmethod
    def in_steady_flow(
        cls,
        flow: SteadyFlow3D,
        grid: UniformGrid3D,
        initial_values: tuple[float, ...],
        *,
        diffusivity: float = 0.0,
        boundary: BoundaryMode3D = "fixed",
        initial_time: float = 0.0,
        name: str = "passive_scalar3d",
    ) -> "PassiveScalarProblem3D":
        time_velocity = TimeDependentVectorField3D(
            evaluator=lambda position, _time: flow.velocity.evaluate(position),
            name=f"{flow.name}.time_independent",
            output_unit=flow.velocity.output_unit,
        )
        return cls(
            flow=UnsteadyFlow3D(time_velocity, name=flow.name),
            grid=grid,
            initial_values=initial_values,
            diffusivity=diffusivity,
            boundary=boundary,
            initial_time=initial_time,
            name=name,
        )


@dataclass(frozen=True, slots=True)
class PassiveScalarSolution3D:
    transport_solution: AdvectionDiffusionSolution3D
    flow_name: str

    @property
    def grid(self) -> UniformGrid3D:
        return self.transport_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.transport_solution.times

    @property
    def states(self) -> tuple[tuple[float, ...], ...]:
        return self.transport_solution.states

    @property
    def duration(self) -> float:
        return self.transport_solution.duration

    @property
    def name(self) -> str:
        return self.transport_solution.name


class FluidTransport3DDomain:
    """3D passive-scalar transport composed from flow kinematics + generic transport PDE."""

    name = "physics.fluid_transport.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.fluid.unsteady_flow3d"),
        DomainDependency("pde.transport3d.problem"),
        DomainDependency("pde.transport3d.solve"),
    )

    def register(self, registry: DomainRegistry) -> None:
        solve_transport = registry.require("pde.transport3d.solve")

        def solve_passive_scalar(
            problem: PassiveScalarProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> PassiveScalarSolution3D:
            transport = solve_transport(
                AdvectionDiffusionProblem3D(
                    grid=problem.grid,
                    initial_values=problem.initial_values,
                    velocity=problem.flow.velocity,
                    diffusivity=problem.diffusivity,
                    boundary=problem.boundary,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return PassiveScalarSolution3D(
                transport_solution=transport,
                flow_name=problem.flow.name,
            )

        registry.register_semantic_type(
            "physics.fluid.passive_scalar_problem3d",
            PassiveScalarProblem3D,
        )
        registry.register_semantic_type(
            "physics.fluid.passive_scalar_solution3d",
            PassiveScalarSolution3D,
        )
        registry.provide("physics.fluid.passive_scalar_problem3d", PassiveScalarProblem3D)
        registry.provide("physics.fluid.passive_scalar_solution3d", PassiveScalarSolution3D)
        registry.provide("physics.fluid.solve_passive_scalar3d", solve_passive_scalar)
