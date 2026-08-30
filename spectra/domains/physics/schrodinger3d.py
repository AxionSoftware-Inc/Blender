from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import REDUCED_PLANCK_CONSTANT
from spectra.core.types import Vec3
from spectra.core.units import ENERGY, MASS, Quantity
from spectra.domains.mathematics.fields import ScalarField3D
from spectra.domains.partial_differential_equations.complex3d import (
    ComplexPDEProblem3D,
    ComplexPDESolution3D,
)
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SchrodingerProblem3D:
    grid: UniformGrid3D
    initial_values: tuple[complex, ...]
    mass: Quantity
    potential: ScalarField3D | None = None
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "schrodinger3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("3D Schrodinger initial sample count must match grid")
        if not all(
            math.isfinite(complex(value).real) and math.isfinite(complex(value).imag)
            for value in self.initial_values
        ):
            raise ValueError("3D Schrodinger initial samples must be finite")
        if self.mass.unit.dimension != MASS or self.mass.si_value <= 0.0:
            raise ValueError("3D Schrodinger mass must be a positive mass quantity")
        if self.potential is not None and self.potential.output_unit is not None:
            if self.potential.output_unit.dimension != ENERGY:
                raise ValueError("3D Schrodinger potential field must use an energy unit")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D Schrodinger boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D Schrodinger initial_time must be finite")
        if not self.name:
            raise ValueError("3D Schrodinger name cannot be empty")


@dataclass(frozen=True, slots=True)
class SchrodingerSolution3D:
    pde_solution: ComplexPDESolution3D
    mass: Quantity
    boundary: BoundaryMode3D

    @property
    def grid(self) -> UniformGrid3D:
        return self.pde_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.pde_solution.times

    @property
    def states(self) -> tuple[tuple[complex, ...], ...]:
        return self.pde_solution.states

    @property
    def duration(self) -> float:
        return self.pde_solution.duration

    @property
    def name(self) -> str:
        return self.pde_solution.name


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


class Schrodinger3DDomain:
    name = "physics.quantum.schrodinger3d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("pde.complex.problem3d"),
        DomainDependency("pde.complex.laplacian_3d"),
        DomainDependency("pde.complex.solve_method_of_lines_3d"),
        DomainDependency("pde.integrate_scalar_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        complex_problem_type = registry.require("pde.complex.problem3d")
        laplacian = registry.require("pde.complex.laplacian_3d")
        solve_complex = registry.require("pde.complex.solve_method_of_lines_3d")
        integrate_scalar = registry.require("pde.integrate_scalar_grid_3d")
        hbar_si = REDUCED_PLANCK_CONSTANT.si_value

        def probability_mass(
            values: tuple[complex, ...],
            grid: UniformGrid3D,
        ) -> float:
            if len(values) != grid.count:
                raise ValueError("3D wavefunction sample count must match grid")
            return float(
                integrate_scalar(
                    tuple(abs(complex(value)) ** 2 for value in values),
                    grid,
                )
            )

        def normalize_samples(
            values: tuple[complex, ...],
            grid: UniformGrid3D,
        ) -> tuple[complex, ...]:
            mass = probability_mass(values, grid)
            if not math.isfinite(mass) or mass <= 0.0:
                raise ValueError("3D wavefunction has zero or invalid probability mass")
            factor = math.sqrt(mass)
            return tuple(complex(value) / factor for value in values)

        def solve_schrodinger(
            problem: SchrodingerProblem3D,
            *,
            end_time: float,
            steps: int = 128,
            normalize_initial: bool = True,
        ) -> SchrodingerSolution3D:
            initial = tuple(complex(value) for value in problem.initial_values)
            if normalize_initial:
                initial = normalize_samples(initial, problem.grid)

            kinetic_coefficient = 1j * hbar_si / (2.0 * problem.mass.si_value)
            coordinates = problem.grid.coordinates

            def rhs(
                _time: float,
                grid: UniformGrid3D,
                values: tuple[complex, ...],
            ) -> tuple[complex, ...]:
                curvature = laplacian(values, grid, boundary=problem.boundary)
                result = []
                for index, (psi, lap) in enumerate(zip(values, curvature, strict=True)):
                    derivative = kinetic_coefficient * lap
                    if problem.potential is not None:
                        potential_joules = problem.potential.evaluate(Vec3(*coordinates[index]))
                        if problem.potential.output_unit is not None:
                            potential_joules = problem.potential.output_unit.to_si(potential_joules)
                        derivative += (-1j * potential_joules / hbar_si) * psi
                    if problem.boundary == "fixed" and _is_boundary(grid, index):
                        derivative = 0.0j
                    result.append(derivative)
                return tuple(result)

            pde_solution = solve_complex(
                complex_problem_type(
                    grid=problem.grid,
                    initial_values=initial,
                    rhs=rhs,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return SchrodingerSolution3D(
                pde_solution=pde_solution,
                mass=problem.mass,
                boundary=problem.boundary,
            )

        registry.register_semantic_type(
            "physics.quantum.schrodinger3d.problem",
            SchrodingerProblem3D,
        )
        registry.register_semantic_type(
            "physics.quantum.schrodinger3d.solution",
            SchrodingerSolution3D,
        )
        registry.provide("physics.quantum.schrodinger3d.problem", SchrodingerProblem3D)
        registry.provide("physics.quantum.schrodinger3d.solution", SchrodingerSolution3D)
        registry.provide("physics.quantum.schrodinger3d.solve", solve_schrodinger)
        registry.provide("physics.quantum.schrodinger3d.probability_mass", probability_mass)
        registry.provide("physics.quantum.schrodinger3d.normalize", normalize_samples)
