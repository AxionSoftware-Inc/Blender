from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import ACCELERATION, DENSITY, KINEMATIC_VISCOSITY, Quantity
from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class IncompressibleFlowProblem3D:
    """Reference constant-density incompressible Navier-Stokes problem in 3D."""

    grid: UniformGrid3D
    initial_velocity: tuple[Vec3, ...]
    density: Quantity
    kinematic_viscosity: Quantity
    velocity_boundary: BoundaryMode3D = "fixed"
    pressure_boundary: BoundaryMode3D = "zero_gradient"
    body_force: TimeDependentVectorField3D | None = None
    initial_time: float = 0.0
    name: str = "incompressible_flow3d"

    def __post_init__(self) -> None:
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("3D initial velocity length must match flow grid")
        if any(not isinstance(vector, Vec3) for vector in self.initial_velocity):
            raise TypeError("3D initial velocity samples must be Vec3")
        if self.density.unit.dimension != DENSITY or self.density.si_value <= 0.0:
            raise ValueError("3D fluid density must be a positive density quantity")
        if (
            self.kinematic_viscosity.unit.dimension != KINEMATIC_VISCOSITY
            or self.kinematic_viscosity.si_value < 0.0
        ):
            raise ValueError(
                "3D kinematic viscosity must be a non-negative kinematic-viscosity quantity"
            )
        if self.velocity_boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D velocity boundary mode: {self.velocity_boundary}")
        if self.pressure_boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D pressure boundary mode: {self.pressure_boundary}")
        if self.body_force is not None and self.body_force.output_unit is not None:
            if self.body_force.output_unit.dimension != ACCELERATION:
                raise ValueError("3D fluid body force field must represent acceleration")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D flow initial_time must be finite")
        if not self.name:
            raise ValueError("3D flow name cannot be empty")


@dataclass(frozen=True, slots=True)
class IncompressibleFlowState3D:
    time: float
    velocity: tuple[Vec3, ...]
    pressure: tuple[float, ...]
    max_divergence: float
    pressure_residual: float
    pressure_converged: bool

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("3D flow state time must be finite")
        if not math.isfinite(self.max_divergence) or self.max_divergence < 0.0:
            raise ValueError("3D flow max_divergence must be finite and non-negative")
        if not math.isfinite(self.pressure_residual) or self.pressure_residual < 0.0:
            raise ValueError("3D flow pressure residual must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class IncompressibleFlowSolution3D:
    grid: UniformGrid3D
    states: tuple[IncompressibleFlowState3D, ...]
    density_si: float
    kinematic_viscosity_si: float
    name: str = "incompressible_flow3d"
    velocity_boundary: BoundaryMode3D = "fixed"
    pressure_boundary: BoundaryMode3D = "zero_gradient"

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("3D flow solution cannot be empty")
        if any(len(state.velocity) != self.grid.count for state in self.states):
            raise ValueError("3D flow velocity state length must match grid")
        if any(len(state.pressure) != self.grid.count for state in self.states):
            raise ValueError("3D flow pressure state length must match grid")
        if any(right.time <= left.time for left, right in zip(self.states, self.states[1:])):
            raise ValueError("3D flow state times must be strictly increasing")

    @property
    def times(self) -> tuple[float, ...]:
        return tuple(state.time for state in self.states)

    @property
    def duration(self) -> float:
        return self.states[-1].time - self.states[0].time


def _is_boundary(grid: UniformGrid3D, index: int) -> bool:
    xy_count = grid.x.count * grid.y.count
    z_index = index // xy_count
    remainder = index % xy_count
    y_index = remainder // grid.x.count
    x_index = remainder % grid.x.count
    return (
        x_index in {0, grid.x.count - 1}
        or y_index in {0, grid.y.count - 1}
        or z_index in {0, grid.z.count - 1}
    )


def _subtract_mean(values: tuple[float, ...]) -> tuple[float, ...]:
    mean = sum(values) / len(values)
    return tuple(value - mean for value in values)


class IncompressibleFlow3DDomain:
    """Projection-method 3D reference solver composed from generic PDE capabilities."""

    name = "physics.incompressible_flow.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("pde.laplacian_3d"),
        DomainDependency("pde.gradient_grid_3d"),
        DomainDependency("pde.divergence_grid_3d"),
        DomainDependency("pde.vector_upwind_advection_grid_3d", min_version=2),
        DomainDependency("pde.poisson_problem3d"),
        DomainDependency("pde.solve_poisson_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        laplacian = registry.require("pde.laplacian_3d")
        gradient = registry.require("pde.gradient_grid_3d")
        divergence = registry.require("pde.divergence_grid_3d")
        vector_advection = registry.require("pde.vector_upwind_advection_grid_3d", min_version=2)
        poisson_problem_type = registry.require("pde.poisson_problem3d")
        solve_poisson = registry.require("pde.solve_poisson_3d")

        def simulate(
            problem: IncompressibleFlowProblem3D,
            *,
            end_time: float,
            steps: int = 60,
            pressure_max_iterations: int = 5_000,
            pressure_tolerance: float = 1e-7,
        ) -> IncompressibleFlowSolution3D:
            if steps < 1:
                raise ValueError("3D flow steps must be >= 1")
            if end_time <= problem.initial_time:
                raise ValueError("3D flow end_time must exceed initial_time")

            dt = (float(end_time) - problem.initial_time) / steps
            density = problem.density.si_value
            viscosity = problem.kinematic_viscosity.si_value
            grid = problem.grid
            velocity = tuple(problem.initial_velocity)
            pressure = tuple(0.0 for _ in range(grid.count))
            initial_boundary_velocity = tuple(problem.initial_velocity)

            initial_divergence = divergence(velocity, grid, boundary=problem.velocity_boundary)
            states = [
                IncompressibleFlowState3D(
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
                    velocity,
                    grid,
                    boundary=problem.velocity_boundary,
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
                lap_w = laplacian(
                    tuple(vector.z for vector in velocity),
                    grid,
                    boundary=problem.velocity_boundary,
                )

                if problem.body_force is None:
                    body_force = tuple(Vec3(0.0, 0.0, 0.0) for _ in range(grid.count))
                else:
                    body_force = tuple(
                        problem.body_force.evaluate(Vec3(x, y, z), time)
                        for x, y, z in grid.coordinates
                    )

                tentative = tuple(
                    Vec3(
                        current.x + dt * (-advective.x + viscosity * diffuse_x + force.x),
                        current.y + dt * (-advective.y + viscosity * diffuse_y + force.y),
                        current.z + dt * (-advective.z + viscosity * diffuse_z + force.z),
                    )
                    for current, advective, diffuse_x, diffuse_y, diffuse_z, force in zip(
                        velocity,
                        advection,
                        lap_u,
                        lap_v,
                        lap_w,
                        body_force,
                        strict=True,
                    )
                )

                if problem.velocity_boundary == "fixed":
                    tentative = tuple(
                        initial_boundary_velocity[index] if _is_boundary(grid, index) else value
                        for index, value in enumerate(tentative)
                    )

                tentative_divergence = divergence(
                    tentative,
                    grid,
                    boundary=problem.velocity_boundary,
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
                    pressure,
                    grid,
                    boundary=problem.pressure_boundary,
                )
                velocity = tuple(
                    Vec3(
                        candidate.x - dt * grad.x / density,
                        candidate.y - dt * grad.y / density,
                        candidate.z - dt * grad.z / density,
                    )
                    for candidate, grad in zip(tentative, pressure_gradient, strict=True)
                )

                if problem.velocity_boundary == "fixed":
                    velocity = tuple(
                        initial_boundary_velocity[index] if _is_boundary(grid, index) else value
                        for index, value in enumerate(velocity)
                    )

                projected_divergence = divergence(
                    velocity,
                    grid,
                    boundary=problem.velocity_boundary,
                )
                states.append(
                    IncompressibleFlowState3D(
                        time=time + dt,
                        velocity=velocity,
                        pressure=pressure,
                        max_divergence=max(abs(value) for value in projected_divergence),
                        pressure_residual=pressure_solution.residual_inf,
                        pressure_converged=pressure_solution.converged,
                    )
                )

            return IncompressibleFlowSolution3D(
                grid=grid,
                states=tuple(states),
                density_si=density,
                kinematic_viscosity_si=viscosity,
                name=problem.name,
                velocity_boundary=problem.velocity_boundary,
                pressure_boundary=problem.pressure_boundary,
            )

        registry.register_semantic_type(
            "physics.incompressible_flow.problem3d",
            IncompressibleFlowProblem3D,
        )
        registry.register_semantic_type(
            "physics.incompressible_flow.state3d",
            IncompressibleFlowState3D,
        )
        registry.register_semantic_type(
            "physics.incompressible_flow.solution3d",
            IncompressibleFlowSolution3D,
        )
        registry.provide("physics.incompressible_flow.problem3d", IncompressibleFlowProblem3D)
        registry.provide("physics.incompressible_flow.state3d", IncompressibleFlowState3D)
        registry.provide("physics.incompressible_flow.solution3d", IncompressibleFlowSolution3D)
        registry.provide("physics.incompressible_flow.simulate3d", simulate)
