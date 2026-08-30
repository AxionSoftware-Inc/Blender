from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import REDUCED_PLANCK_CONSTANT
from spectra.core.types import Vec2
from spectra.core.units import ENERGY, MASS, Quantity
from spectra.domains.mathematics.fields2d import ScalarField2D
from spectra.domains.partial_differential_equations.complex2d import (
    ComplexPDEProblem2D,
    ComplexPDESolution2D,
)
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SchrodingerProblem2D:
    grid: UniformGrid2D
    initial_values: tuple[complex, ...]
    mass: Quantity
    potential: ScalarField2D | None = None
    boundary: BoundaryMode2D = "fixed"
    initial_time: float = 0.0
    name: str = "schrodinger2d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("2D Schrodinger initial sample count must match grid")
        if not all(
            math.isfinite(complex(value).real) and math.isfinite(complex(value).imag)
            for value in self.initial_values
        ):
            raise ValueError("2D Schrodinger initial samples must be finite")
        if self.mass.unit.dimension != MASS or self.mass.si_value <= 0.0:
            raise ValueError("2D Schrodinger mass must be a positive mass quantity")
        if self.potential is not None and self.potential.output_unit is not None:
            if self.potential.output_unit.dimension != ENERGY:
                raise ValueError("2D Schrodinger potential field must use an energy unit")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 2D Schrodinger boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("2D Schrodinger initial_time must be finite")
        if not self.name:
            raise ValueError("2D Schrodinger name cannot be empty")


@dataclass(frozen=True, slots=True)
class SchrodingerSolution2D:
    pde_solution: ComplexPDESolution2D
    mass: Quantity
    boundary: BoundaryMode2D

    @property
    def grid(self) -> UniformGrid2D:
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


def _is_boundary(grid: UniformGrid2D, index: int) -> bool:
    x_index = index % grid.x.count
    y_index = index // grid.x.count
    return x_index in {0, grid.x.count - 1} or y_index in {0, grid.y.count - 1}


class Schrodinger2DDomain:
    name = "physics.quantum.schrodinger2d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.scalar_field2d"),
        DomainDependency("pde.complex.problem2d"),
        DomainDependency("pde.complex.laplacian_2d"),
        DomainDependency("pde.complex.solve_method_of_lines_2d"),
        DomainDependency("pde.integrate_scalar_grid_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        complex_problem_type = registry.require("pde.complex.problem2d")
        laplacian = registry.require("pde.complex.laplacian_2d")
        solve_complex = registry.require("pde.complex.solve_method_of_lines_2d")
        integrate_scalar = registry.require("pde.integrate_scalar_grid_2d")
        hbar_si = REDUCED_PLANCK_CONSTANT.si_value

        def probability_mass(
            values: tuple[complex, ...],
            grid: UniformGrid2D,
        ) -> float:
            if len(values) != grid.count:
                raise ValueError("2D wavefunction sample count must match grid")
            return float(
                integrate_scalar(
                    tuple(abs(complex(value)) ** 2 for value in values),
                    grid,
                )
            )

        def normalize_samples(
            values: tuple[complex, ...],
            grid: UniformGrid2D,
        ) -> tuple[complex, ...]:
            mass = probability_mass(values, grid)
            if not math.isfinite(mass) or mass <= 0.0:
                raise ValueError("2D wavefunction has zero or invalid probability mass")
            factor = math.sqrt(mass)
            return tuple(complex(value) / factor for value in values)

        def solve_schrodinger(
            problem: SchrodingerProblem2D,
            *,
            end_time: float,
            steps: int = 256,
            normalize_initial: bool = True,
        ) -> SchrodingerSolution2D:
            initial = tuple(complex(value) for value in problem.initial_values)
            if normalize_initial:
                initial = normalize_samples(initial, problem.grid)

            kinetic_coefficient = 1j * hbar_si / (2.0 * problem.mass.si_value)
            coordinates = problem.grid.coordinates

            def rhs(
                _time: float,
                grid: UniformGrid2D,
                values: tuple[complex, ...],
            ) -> tuple[complex, ...]:
                curvature = laplacian(values, grid, boundary=problem.boundary)
                result = []
                for index, (psi, lap) in enumerate(zip(values, curvature, strict=True)):
                    derivative = kinetic_coefficient * lap
                    if problem.potential is not None:
                        potential_joules = problem.potential.evaluate(
                            Vec2(*coordinates[index])
                        )
                        if problem.potential.output_unit is not None:
                            potential_joules = problem.potential.output_unit.to_si(
                                potential_joules
                            )
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
            return SchrodingerSolution2D(
                pde_solution=pde_solution,
                mass=problem.mass,
                boundary=problem.boundary,
            )

        def compile_solution(solution: SchrodingerSolution2D):
            return registry.compile_scene(solution.pde_solution)

        registry.register_semantic_type(
            "physics.quantum.schrodinger2d.problem",
            SchrodingerProblem2D,
        )
        registry.register_semantic_type(
            "physics.quantum.schrodinger2d.solution",
            SchrodingerSolution2D,
        )
        registry.provide("physics.quantum.schrodinger2d.problem", SchrodingerProblem2D)
        registry.provide("physics.quantum.schrodinger2d.solve", solve_schrodinger)
        registry.provide("physics.quantum.schrodinger2d.probability_mass", probability_mass)
        registry.provide("physics.quantum.schrodinger2d.normalize", normalize_samples)
        registry.register_visualization(SchrodingerSolution2D, compile_solution)
