from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import VACUUM_PERMITTIVITY
from spectra.core.types import Vec3
from spectra.core.units import (
    CHARGE,
    LENGTH,
    NEWTON_PER_COULOMB,
    VOLT,
    Unit,
    COULOMB,
    METER,
)
from spectra.domains.mathematics.fields import ScalarField3D, VectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


CHARGE_DENSITY_DIMENSION = CHARGE / (LENGTH ** 3)
COULOMB_PER_CUBIC_METER = COULOMB / (METER ** 3)


@dataclass(frozen=True, slots=True)
class ElectrostaticPotentialProblem3D:
    """Electrostatic Poisson problem on a regular 3D grid.

    Charge-density samples are volume density values. Potential values are SI
    volts internally. Fixed boundaries preserve `potential_initial_values` at
    the outer grid cells; periodic/zero-gradient problems require the usual
    zero-mean Poisson compatibility and are mean-centered before solving.
    """

    grid: UniformGrid3D
    charge_density: tuple[float, ...]
    charge_density_unit: Unit = COULOMB_PER_CUBIC_METER
    boundary: BoundaryMode3D = "fixed"
    potential_initial_values: tuple[float, ...] | None = None
    name: str = "electrostatic_potential3d"

    def __post_init__(self) -> None:
        if len(self.charge_density) != self.grid.count:
            raise ValueError("charge-density sample count must match 3D grid")
        if not all(math.isfinite(float(value)) for value in self.charge_density):
            raise ValueError("charge-density samples must be finite")
        if self.charge_density_unit.dimension != CHARGE_DENSITY_DIMENSION:
            raise ValueError("charge-density unit has incompatible dimension")
        if self.potential_initial_values is not None:
            if len(self.potential_initial_values) != self.grid.count:
                raise ValueError("electrostatic potential initial values must match grid")
            if not all(math.isfinite(float(value)) for value in self.potential_initial_values):
                raise ValueError("electrostatic potential initial values must be finite")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown electrostatic boundary mode: {self.boundary}")
        if not self.name:
            raise ValueError("electrostatic potential name cannot be empty")


@dataclass(frozen=True, slots=True)
class ElectrostaticPotentialSolution3D:
    grid: UniformGrid3D
    potential_volts: tuple[float, ...]
    electric_field_si: tuple[Vec3, ...]
    residual_inf: float
    converged: bool
    name: str = "electrostatic_potential3d"

    def __post_init__(self) -> None:
        if len(self.potential_volts) != self.grid.count:
            raise ValueError("electrostatic potential sample count must match grid")
        if len(self.electric_field_si) != self.grid.count:
            raise ValueError("electric-field sample count must match grid")
        if not math.isfinite(self.residual_inf) or self.residual_inf < 0.0:
            raise ValueError("electrostatic residual must be finite and non-negative")


class ElectrostaticPotential3DDomain:
    """3D electrostatics composed from generic elliptic/PDE field capabilities."""

    name = "physics.electrostatic_potential.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.poisson_problem3d"),
        DomainDependency("pde.solve_poisson_3d"),
        DomainDependency("pde.gradient_grid_3d"),
        DomainDependency("pde.scalar_field_from_grid_3d"),
        DomainDependency("pde.vector_field_from_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        poisson_problem_type = registry.require("pde.poisson_problem3d")
        solve_poisson = registry.require("pde.solve_poisson_3d")
        gradient = registry.require("pde.gradient_grid_3d")
        scalar_adapter = registry.require("pde.scalar_field_from_grid_3d")
        vector_adapter = registry.require("pde.vector_field_from_grid_3d")

        def solve_electrostatic_potential(
            problem: ElectrostaticPotentialProblem3D,
            *,
            max_iterations: int = 10_000,
            tolerance: float = 1e-8,
        ) -> ElectrostaticPotentialSolution3D:
            density_si = tuple(
                problem.charge_density_unit.to_si(value)
                for value in problem.charge_density
            )
            source = tuple(-value / VACUUM_PERMITTIVITY.si_value for value in density_si)
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
            potential_gradient = gradient(
                poisson.values,
                problem.grid,
                boundary=problem.boundary,
            )
            electric_field = tuple(
                Vec3(-value.x, -value.y, -value.z)
                for value in potential_gradient
            )
            return ElectrostaticPotentialSolution3D(
                grid=problem.grid,
                potential_volts=poisson.values,
                electric_field_si=electric_field,
                residual_inf=poisson.residual_inf,
                converged=poisson.converged,
                name=problem.name,
            )

        def potential_field(solution: ElectrostaticPotentialSolution3D) -> ScalarField3D:
            return scalar_adapter(
                solution.grid,
                solution.potential_volts,
                name=f"{solution.name}.potential",
                output_unit=VOLT,
                outside="clamp",
            )

        def electric_field(solution: ElectrostaticPotentialSolution3D) -> VectorField3D:
            return vector_adapter(
                solution.grid,
                solution.electric_field_si,
                name=f"{solution.name}.electric_field",
                output_unit=NEWTON_PER_COULOMB,
                outside="clamp",
            )

        registry.register_semantic_type(
            "physics.electrostatic_potential.problem3d",
            ElectrostaticPotentialProblem3D,
        )
        registry.register_semantic_type(
            "physics.electrostatic_potential.solution3d",
            ElectrostaticPotentialSolution3D,
        )
        registry.provide(
            "physics.electrostatic_potential.problem3d",
            ElectrostaticPotentialProblem3D,
        )
        registry.provide(
            "physics.electrostatic_potential.solve3d",
            solve_electrostatic_potential,
        )
        registry.provide(
            "physics.electrostatic_potential.scalar_field3d",
            potential_field,
        )
        registry.provide(
            "physics.electrostatic_potential.vector_field3d",
            electric_field,
        )
