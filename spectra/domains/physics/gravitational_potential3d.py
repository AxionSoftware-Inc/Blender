from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import GRAVITATIONAL_CONSTANT
from spectra.core.types import Vec3
from spectra.core.units import (
    DENSITY,
    JOULE,
    KILOGRAM,
    KILOGRAM_PER_CUBIC_METER,
    METER_PER_SECOND_SQUARED,
    Unit,
)
from spectra.domains.mathematics.fields import ScalarField3D, VectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


GRAVITATIONAL_POTENTIAL_UNIT = JOULE / KILOGRAM


@dataclass(frozen=True, slots=True)
class GravitationalPotentialProblem3D:
    grid: UniformGrid3D
    mass_density: tuple[float, ...]
    mass_density_unit: Unit = KILOGRAM_PER_CUBIC_METER
    boundary: BoundaryMode3D = "fixed"
    potential_initial_values: tuple[float, ...] | None = None
    name: str = "gravitational_potential3d"

    def __post_init__(self) -> None:
        if len(self.mass_density) != self.grid.count:
            raise ValueError("mass-density sample count must match 3D grid")
        if not all(math.isfinite(float(value)) for value in self.mass_density):
            raise ValueError("mass-density samples must be finite")
        if self.mass_density_unit.dimension != DENSITY:
            raise ValueError("mass-density unit has incompatible dimension")
        if self.potential_initial_values is not None:
            if len(self.potential_initial_values) != self.grid.count:
                raise ValueError("gravitational potential initial values must match grid")
            if not all(math.isfinite(float(value)) for value in self.potential_initial_values):
                raise ValueError("gravitational potential initial values must be finite")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown gravitational boundary mode: {self.boundary}")
        if not self.name:
            raise ValueError("gravitational potential name cannot be empty")


@dataclass(frozen=True, slots=True)
class GravitationalPotentialSolution3D:
    grid: UniformGrid3D
    potential_si: tuple[float, ...]
    field_si: tuple[Vec3, ...]
    residual_inf: float
    converged: bool
    name: str = "gravitational_potential3d"

    def __post_init__(self) -> None:
        if len(self.potential_si) != self.grid.count:
            raise ValueError("gravitational potential sample count must match grid")
        if len(self.field_si) != self.grid.count:
            raise ValueError("gravitational field sample count must match grid")
        if not math.isfinite(self.residual_inf) or self.residual_inf < 0.0:
            raise ValueError("gravitational residual must be finite and non-negative")


class GravitationalPotential3DDomain:
    name = "physics.gravitational_potential.3d"
    version = "2"
    dependencies = (
        DomainDependency("physics.potential_field3d"),
        DomainDependency("pde.poisson_problem3d"),
        DomainDependency("pde.solve_poisson_3d"),
        DomainDependency("pde.gradient_grid_3d"),
        DomainDependency("pde.scalar_field_from_grid_3d"),
        DomainDependency("pde.vector_field_from_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        potential_field_type = registry.require("physics.potential_field3d")
        poisson_problem_type = registry.require("pde.poisson_problem3d")
        solve_poisson = registry.require("pde.solve_poisson_3d")
        gradient = registry.require("pde.gradient_grid_3d")
        scalar_adapter = registry.require("pde.scalar_field_from_grid_3d")
        vector_adapter = registry.require("pde.vector_field_from_grid_3d")

        def solve_gravity(
            problem: GravitationalPotentialProblem3D,
            *,
            max_iterations: int = 10_000,
            tolerance: float = 1e-8,
        ) -> GravitationalPotentialSolution3D:
            density_si = tuple(
                problem.mass_density_unit.to_si(value)
                for value in problem.mass_density
            )
            source = tuple(
                4.0 * math.pi * GRAVITATIONAL_CONSTANT.si_value * density
                for density in density_si
            )
            if problem.boundary in {"periodic", "zero_gradient"}:
                mean = sum(source) / len(source)
                source = tuple(value - mean for value in source)

            poisson = solve_poisson(
                poisson_problem_type(
                    grid=problem.grid,
                    source=source,
                    boundary=problem.boundary,
                    initial_values=problem.potential_initial_values,
                    name=f"{problem.name}.potential",
                ),
                max_iterations=max_iterations,
                tolerance=tolerance,
            )
            grad = gradient(
                poisson.values,
                problem.grid,
                boundary=problem.boundary,
            )
            field = tuple(Vec3(-value.x, -value.y, -value.z) for value in grad)
            return GravitationalPotentialSolution3D(
                grid=problem.grid,
                potential_si=poisson.values,
                field_si=field,
                residual_inf=poisson.residual_inf,
                converged=poisson.converged,
                name=problem.name,
            )

        def potential_field(solution: GravitationalPotentialSolution3D) -> ScalarField3D:
            return scalar_adapter(
                solution.grid,
                solution.potential_si,
                name=f"{solution.name}.potential",
                output_unit=GRAVITATIONAL_POTENTIAL_UNIT,
                outside="clamp",
            )

        def gravitational_field(solution: GravitationalPotentialSolution3D) -> VectorField3D:
            return vector_adapter(
                solution.grid,
                solution.field_si,
                name=f"{solution.name}.field",
                output_unit=METER_PER_SECOND_SQUARED,
                outside="clamp",
            )

        def potential_model(solution: GravitationalPotentialSolution3D):
            return potential_field_type(
                potential=potential_field(solution),
                field=gravitational_field(solution),
                name=solution.name,
            )

        registry.register_semantic_type(
            "physics.gravitational_potential.problem3d",
            GravitationalPotentialProblem3D,
        )
        registry.register_semantic_type(
            "physics.gravitational_potential.solution3d",
            GravitationalPotentialSolution3D,
        )
        registry.provide(
            "physics.gravitational_potential.problem3d",
            GravitationalPotentialProblem3D,
        )
        registry.provide("physics.gravitational_potential.solve3d", solve_gravity)
        registry.provide(
            "physics.gravitational_potential.scalar_field3d",
            potential_field,
        )
        registry.provide(
            "physics.gravitational_potential.vector_field3d",
            gravitational_field,
        )
        registry.provide(
            "physics.gravitational_potential.potential_field3d",
            potential_model,
            version=2,
        )
