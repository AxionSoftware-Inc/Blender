from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import VACUUM_PERMITTIVITY
from spectra.core.types import Vec2
from spectra.core.units import (
    CHARGE,
    LENGTH,
    NEWTON_PER_COULOMB,
    VOLT,
    Unit,
    COULOMB,
    METER,
)
from spectra.domains.mathematics.fields2d import ScalarField2D, VectorField2D
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


CHARGE_DENSITY_DIMENSION = CHARGE / (LENGTH ** 3)
COULOMB_PER_CUBIC_METER = COULOMB / (METER ** 3)


@dataclass(frozen=True, slots=True)
class ElectrostaticPotentialProblem2D:
    """Translationally-invariant 2D slice of Poisson electrostatics.

    Charge-density samples are interpreted as volume density in the supplied
    unit. Potential boundary/initial values are volts.
    """

    grid: UniformGrid2D
    charge_density: tuple[float, ...]
    charge_density_unit: Unit = COULOMB_PER_CUBIC_METER
    boundary: BoundaryMode2D = "fixed"
    potential_initial_values: tuple[float, ...] | None = None
    name: str = "electrostatic_potential2d"

    def __post_init__(self) -> None:
        if len(self.charge_density) != self.grid.count:
            raise ValueError("charge-density sample count must match grid")
        if not all(math.isfinite(float(value)) for value in self.charge_density):
            raise ValueError("charge-density samples must be finite")
        if self.charge_density_unit.dimension != CHARGE_DENSITY_DIMENSION:
            raise ValueError("charge-density unit has incompatible dimension")
        if self.potential_initial_values is not None:
            if len(self.potential_initial_values) != self.grid.count:
                raise ValueError("potential initial values must match grid")
            if not all(math.isfinite(float(value)) for value in self.potential_initial_values):
                raise ValueError("potential initial values must be finite")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown electrostatic boundary mode: {self.boundary}")
        if not self.name:
            raise ValueError("electrostatic problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ElectrostaticPotentialSolution2D:
    grid: UniformGrid2D
    potential_volts: tuple[float, ...]
    electric_field_si: tuple[Vec2, ...]
    residual_inf: float
    converged: bool
    name: str = "electrostatic_potential2d"

    def __post_init__(self) -> None:
        if len(self.potential_volts) != self.grid.count:
            raise ValueError("potential sample count must match grid")
        if len(self.electric_field_si) != self.grid.count:
            raise ValueError("electric-field sample count must match grid")
        if not math.isfinite(self.residual_inf) or self.residual_inf < 0.0:
            raise ValueError("electrostatic residual must be finite and non-negative")

    def _nearest_index(self, position: Vec2) -> int:
        x_values = self.grid.x.coordinates
        y_values = self.grid.y.coordinates
        x_index = min(range(len(x_values)), key=lambda index: abs(x_values[index] - position.x))
        y_index = min(range(len(y_values)), key=lambda index: abs(y_values[index] - position.y))
        return self.grid.flat_index(x_index, y_index)

    def nearest_potential_field(self) -> ScalarField2D:
        return ScalarField2D(
            evaluator=lambda position: self.potential_volts[self._nearest_index(position)],
            name=f"{self.name}.potential.nearest",
            output_unit=VOLT,
        )

    def nearest_electric_field(self) -> VectorField2D:
        return VectorField2D(
            evaluator=lambda position: self.electric_field_si[self._nearest_index(position)],
            name=f"{self.name}.electric_field.nearest",
            output_unit=NEWTON_PER_COULOMB,
        )


class ElectrostaticPotential2DDomain:
    """Electrostatic potential composed from generic Poisson and grid-gradient capabilities."""

    name = "physics.electrostatic_potential.2d"
    version = "2"
    dependencies = (
        DomainDependency("mathematics.scalar_field2d"),
        DomainDependency("mathematics.vector_field2d"),
        DomainDependency("pde.poisson_problem2d"),
        DomainDependency("pde.solve_poisson_2d"),
        DomainDependency("pde.gradient_grid_2d"),
        DomainDependency("pde.scalar_field_from_grid_2d"),
        DomainDependency("pde.vector_field_from_grid_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        poisson_problem_type = registry.require("pde.poisson_problem2d")
        solve_poisson = registry.require("pde.solve_poisson_2d")
        gradient = registry.require("pde.gradient_grid_2d")
        scalar_field_from_grid = registry.require("pde.scalar_field_from_grid_2d")
        vector_field_from_grid = registry.require("pde.vector_field_from_grid_2d")

        def solve_electrostatic_potential(
            problem: ElectrostaticPotentialProblem2D,
            *,
            max_iterations: int = 10_000,
            tolerance: float = 1e-8,
        ) -> ElectrostaticPotentialSolution2D:
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
            electric_field = tuple(Vec2(-value.x, -value.y) for value in potential_gradient)
            return ElectrostaticPotentialSolution2D(
                grid=problem.grid,
                potential_volts=poisson.values,
                electric_field_si=electric_field,
                residual_inf=poisson.residual_inf,
                converged=poisson.converged,
                name=problem.name,
            )

        def potential_field(
            solution: ElectrostaticPotentialSolution2D,
            *,
            outside: str = "clamp",
        ) -> ScalarField2D:
            return scalar_field_from_grid(
                solution.grid,
                solution.potential_volts,
                name=f"{solution.name}.potential",
                output_unit=VOLT,
                outside=outside,
            )

        def electric_field(
            solution: ElectrostaticPotentialSolution2D,
            *,
            outside: str = "clamp",
        ) -> VectorField2D:
            return vector_field_from_grid(
                solution.grid,
                solution.electric_field_si,
                name=f"{solution.name}.electric_field",
                output_unit=NEWTON_PER_COULOMB,
                outside=outside,
            )

        registry.register_semantic_type(
            "physics.electrostatic_potential.problem2d",
            ElectrostaticPotentialProblem2D,
        )
        registry.register_semantic_type(
            "physics.electrostatic_potential.solution2d",
            ElectrostaticPotentialSolution2D,
        )
        registry.provide(
            "physics.electrostatic_potential.problem2d",
            ElectrostaticPotentialProblem2D,
        )
        registry.provide(
            "physics.electrostatic_potential.solve2d",
            solve_electrostatic_potential,
        )
        registry.provide(
            "physics.electrostatic_potential.potential_field",
            potential_field,
            version=2,
        )
        registry.provide(
            "physics.electrostatic_potential.electric_field",
            electric_field,
            version=2,
        )
