from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec2
from spectra.core.units import (
    ACCELERATION,
    DENSITY,
    KINEMATIC_VISCOSITY,
    Quantity,
)
from spectra.domains.mathematics.fields2d import TimeDependentVectorField2D
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class IncompressibleFlowProblem2D:
    """Reference constant-density incompressible Navier-Stokes problem."""

    grid: UniformGrid2D
    initial_velocity: tuple[Vec2, ...]
    density: Quantity
    kinematic_viscosity: Quantity
    velocity_boundary: BoundaryMode2D = "fixed"
    pressure_boundary: BoundaryMode2D = "zero_gradient"
    body_force: TimeDependentVectorField2D | None = None
    initial_time: float = 0.0
    name: str = "incompressible_flow2d"

    def __post_init__(self) -> None:
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("initial velocity length must match flow grid")
        if any(not isinstance(vector, Vec2) for vector in self.initial_velocity):
            raise TypeError("initial velocity samples must be Vec2")
        if self.density.unit.dimension != DENSITY or self.density.si_value <= 0.0:
            raise ValueError("fluid density must be a positive density quantity")
        if (
            self.kinematic_viscosity.unit.dimension != KINEMATIC_VISCOSITY
            or self.kinematic_viscosity.si_value < 0.0
        ):
            raise ValueError(
                "kinematic viscosity must be a non-negative kinematic-viscosity quantity"
            )
        if self.velocity_boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown velocity boundary mode: {self.velocity_boundary}")
        if self.pressure_boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown pressure boundary mode: {self.pressure_boundary}")
        if self.body_force is not None and self.body_force.output_unit is not None:
            if self.body_force.output_unit.dimension != ACCELERATION:
                raise ValueError("fluid body force field must represent acceleration")
        if not math.isfinite(self.initial_time):
            raise ValueError("flow initial_time must be finite")
        if not self.name:
            raise ValueError("flow name cannot be empty")


@dataclass(frozen=True, slots=True)
class IncompressibleFlowState2D:
    time: float
    velocity: tuple[Vec2, ...]
    pressure: tuple[float, ...]
    max_divergence: float
    pressure_residual: float
    pressure_converged: bool

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("flow state time must be finite")
        if not math.isfinite(self.max_divergence) or self.max_divergence < 0.0:
            raise ValueError("flow max_divergence must be finite and non-negative")
        if not math.isfinite(self.pressure_residual) or self.pressure_residual < 0.0:
            raise ValueError("flow pressure residual must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class IncompressibleFlowSolution2D:
    grid: UniformGrid2D
    states: tuple[IncompressibleFlowState2D, ...]
    density_si: float
    kinematic_viscosity_si: float
    name: str = "incompressible_flow2d"
    velocity_boundary: BoundaryMode2D = "fixed"
    pressure_boundary: BoundaryMode2D = "zero_gradient"

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("flow solution cannot be empty")
        if any(len(state.velocity) != self.grid.count for state in self.states):
            raise ValueError("flow velocity state length must match grid")
        if any(len(state.pressure) != self.grid.count for state in self.states):
            raise ValueError("flow pressure state length must match grid")
        if any(right.time <= left.time for left, right in zip(self.states, self.states[1:])):
            raise ValueError("flow state times must be strictly increasing")
        if self.velocity_boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown velocity boundary mode: {self.velocity_boundary}")
        if self.pressure_boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown pressure boundary mode: {self.pressure_boundary}")

    @property
    def times(self) -> tuple[float, ...]:
        return tuple(state.time for state in self.states)

    @property
    def duration(self) -> float:
        return self.states[-1].time - self.states[0].time


def _is_boundary(grid: UniformGrid2D, index: int) -> bool:
    x_index = index % grid.x.count
    y_index = index // grid.x.count
    return x_index in {0, grid.x.count - 1} or y_index in {0, grid.y.count - 1}


def _subtract_mean(values: tuple[float, ...]) -> tuple[float, ...]:
    mean = sum(values) / len(values)
    return tuple(value - mean for value in values)


class IncompressibleFlow2DDomain:
    """Projection-method reference solver composed from generic PDE capabilities."""

    name = "physics.incompressible_flow.2d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("pde.laplacian_2d"),
        DomainDependency("pde.gradient_grid_2d"),
        DomainDependency("pde.divergence_grid_2d"),
        DomainDependency("pde.vector_upwind_advection_grid_2d"),
        DomainDependency("pde.poisson_problem2d"),
        DomainDependency("pde.solve_poisson_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.physics.incompressible_flow_visualization import (
            compile_incompressible_flow_scene,
        )

        laplacian = registry.require("pde.laplacian_2d")
        gradient = registry.require("pde.gradient_grid_2d")
        divergence = registry.require("pde.divergence_grid_2d")
        vector_advection = registry.require("pde.vector_upwind_advection_grid_2d")
        poisson_problem_type = registry.require("pde.poisson_problem2d")
        solve_poisson = registry.require("pde.solve_poisson_2d")

        def simulate(
            problem: IncompressibleFlowProblem2D,
            *,
            end_time: float,
            steps: int = 120,
            pressure_max_iterations: int = 5_000,
            pressure_tolerance: float = 1e-7,
        ) -> IncompressibleFlowSolution2D:
            if steps < 1:
                raise ValueError("flow steps must be >= 1")
            if end_time <= problem.initial_time:
                raise ValueError("flow end_time must exceed initial_time")

            dt = (float(end_time) - problem.initial_time) / steps
            density = problem.density.si_value
            viscosity = problem.kinematic_viscosity.si_value
            grid = problem.grid
            velocity = tuple(problem.initial_velocity)
            pressure = tuple(0.0 for _ in range(grid.count))
            initial_boundary_velocity = tuple(problem.initial_velocity)

            initial_divergence = divergence(velocity, grid, boundary=problem.velocity_boundary)
            states = [
                IncompressibleFlowState2D(
                    time=problem.initial_time,
                    velocity=velocity,
                    pressure=pressure,
                    max_divergence=max(abs(value) for value in initial_divergence),
                    pressure_residual=0.0,
                    pressure_converged=True,
                )
            ]

            for step_index in range(steps):
                time = problem.initial_time + step_index * dt
                advection = vector_advection(
                    velocity, grid, boundary=problem.velocity_boundary
                )
                lap_u = laplacian(
                    tuple(vector.x for vector in velocity),
                    grid,
                    boundary=problem.velocity_boundary,
                )
                lap_v = laplacian(
                    tuple(vector.y for vector in velocity),
                    grid,
                    boundary=problem.velocity_boundary,
                )

                if problem.body_force is None:
                    body_force = tuple(Vec2(0.0, 0.0) for _ in range(grid.count))
                else:
                    body_force = tuple(
                        problem.body_force.evaluate(Vec2(x, y), time)
                        for x, y in grid.coordinates
                    )

                tentative = tuple(
                    Vec2(
                        current.x + dt * (-advective.x + viscosity * diffuse_x + force.x),
                        current.y + dt * (-advective.y + viscosity * diffuse_y + force.y),
                    )
                    for current, advective, diffuse_x, diffuse_y, force in zip(
                        velocity, advection, lap_u, lap_v, body_force, strict=True
                    )
                )

                if problem.velocity_boundary == "fixed":
                    tentative = tuple(
                        initial_boundary_velocity[index] if _is_boundary(grid, index) else value
                        for index, value in enumerate(tentative)
                    )

                tentative_divergence = divergence(
                    tentative, grid, boundary=problem.velocity_boundary
                )
                pressure_source = tuple(density * value / dt for value in tentative_divergence)
                if problem.pressure_boundary in {"periodic", "zero_gradient"}:
                    pressure_source = _subtract_mean(pressure_source)

                pressure_solution = solve_poisson(
                    poisson_problem_type(
                        grid=grid,
                        source=pressure_source,
                        boundary=problem.pressure_boundary,
                        initial_values=pressure,
                        name=f"{problem.name}.pressure",
                    ),
                    max_iterations=pressure_max_iterations,
                    tolerance=pressure_tolerance,
                )
                pressure = pressure_solution.values
                pressure_gradient = gradient(
                    pressure, grid, boundary=problem.pressure_boundary
                )
                velocity = tuple(
                    Vec2(
                        candidate.x - dt * grad.x / density,
                        candidate.y - dt * grad.y / density,
                    )
                    for candidate, grad in zip(tentative, pressure_gradient, strict=True)
                )

                if problem.velocity_boundary == "fixed":
                    velocity = tuple(
                        initial_boundary_velocity[index] if _is_boundary(grid, index) else value
                        for index, value in enumerate(velocity)
                    )

                projected_divergence = divergence(
                    velocity, grid, boundary=problem.velocity_boundary
                )
                states.append(
                    IncompressibleFlowState2D(
                        time=time + dt,
                        velocity=velocity,
                        pressure=pressure,
                        max_divergence=max(abs(value) for value in projected_divergence),
                        pressure_residual=pressure_solution.residual_inf,
                        pressure_converged=pressure_solution.converged,
                    )
                )

            return IncompressibleFlowSolution2D(
                grid=grid,
                states=tuple(states),
                density_si=density,
                kinematic_viscosity_si=viscosity,
                name=problem.name,
                velocity_boundary=problem.velocity_boundary,
                pressure_boundary=problem.pressure_boundary,
            )

        registry.register_semantic_type(
            "physics.incompressible_flow.problem2d", IncompressibleFlowProblem2D
        )
        registry.register_semantic_type(
            "physics.incompressible_flow.state2d", IncompressibleFlowState2D
        )
        registry.register_semantic_type(
            "physics.incompressible_flow.solution2d", IncompressibleFlowSolution2D
        )
        registry.provide("physics.incompressible_flow.problem2d", IncompressibleFlowProblem2D)
        registry.provide("physics.incompressible_flow.state2d", IncompressibleFlowState2D, version=2)
        registry.provide("physics.incompressible_flow.solution2d", IncompressibleFlowSolution2D, version=2)
        registry.provide("physics.incompressible_flow.simulate2d", simulate, version=2)
        registry.register_visualization(IncompressibleFlowSolution2D, compile_incompressible_flow_scene)
