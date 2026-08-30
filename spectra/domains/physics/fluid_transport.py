from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.partial_differential_equations.transport2d import (
    AdvectionDiffusionProblem2D,
    AdvectionDiffusionSolution2D,
)
from spectra.domains.physics.fluid_kinematics import SteadyFlow2D, UnsteadyFlow2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PassiveScalarProblem2D:
    flow: UnsteadyFlow2D
    grid: UniformGrid2D
    initial_values: tuple[float, ...]
    diffusivity: float = 0.0
    boundary: BoundaryMode2D = "fixed"
    initial_time: float = 0.0
    name: str = "passive_scalar2d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("passive scalar initial_values length must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("passive scalar initial values must be finite")
        if not math.isfinite(self.diffusivity) or self.diffusivity < 0.0:
            raise ValueError("passive scalar diffusivity must be finite and non-negative")
        if not math.isfinite(self.initial_time):
            raise ValueError("passive scalar initial_time must be finite")
        if not self.name:
            raise ValueError("passive scalar name cannot be empty")

    @classmethod
    def in_steady_flow(
        cls,
        flow: SteadyFlow2D,
        grid: UniformGrid2D,
        initial_values: tuple[float, ...],
        *,
        diffusivity: float = 0.0,
        boundary: BoundaryMode2D = "fixed",
        initial_time: float = 0.0,
        name: str = "passive_scalar2d",
    ) -> "PassiveScalarProblem2D":
        from spectra.domains.mathematics.fields2d import TimeDependentVectorField2D

        time_velocity = TimeDependentVectorField2D(
            evaluator=lambda position, _time: flow.velocity.evaluate(position),
            name=f"{flow.name}.time_independent",
            output_unit=flow.velocity.output_unit,
        )
        return cls(
            flow=UnsteadyFlow2D(time_velocity, name=flow.name),
            grid=grid,
            initial_values=initial_values,
            diffusivity=diffusivity,
            boundary=boundary,
            initial_time=initial_time,
            name=name,
        )


@dataclass(frozen=True, slots=True)
class PassiveScalarSolution2D:
    transport_solution: AdvectionDiffusionSolution2D
    flow_name: str

    @property
    def grid(self) -> UniformGrid2D:
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


class FluidTransport2DDomain:
    """Passive scalar transport composed from fluid kinematics + generic PDE transport."""

    name = "physics.fluid_transport.2d"
    version = "1"
    dependencies = (
        DomainDependency("physics.fluid.unsteady_flow2d"),
        DomainDependency("pde.transport2d.problem"),
        DomainDependency("pde.transport2d.solve"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization2d import (
            compile_scalar_pde_solution_2d_scene,
        )

        solve_transport = registry.require("pde.transport2d.solve")

        def solve_passive_scalar(
            problem: PassiveScalarProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> PassiveScalarSolution2D:
            transport = solve_transport(
                AdvectionDiffusionProblem2D(
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
            return PassiveScalarSolution2D(
                transport_solution=transport,
                flow_name=problem.flow.name,
            )

        def compile_solution(solution: PassiveScalarSolution2D):
            return compile_scalar_pde_solution_2d_scene(solution.transport_solution.pde_solution)

        registry.register_semantic_type("physics.fluid.passive_scalar_problem2d", PassiveScalarProblem2D)
        registry.register_semantic_type("physics.fluid.passive_scalar_solution2d", PassiveScalarSolution2D)
        registry.provide("physics.fluid.passive_scalar_problem2d", PassiveScalarProblem2D)
        registry.provide("physics.fluid.solve_passive_scalar2d", solve_passive_scalar)
        registry.register_visualization(PassiveScalarSolution2D, compile_solution)
