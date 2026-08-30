from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import REDUCED_PLANCK_CONSTANT
from spectra.core.units import MASS, Quantity
from spectra.domains.mathematics import RealFunction1D
from spectra.domains.partial_differential_equations import (
    BoundaryMode1D,
    ComplexPDEProblem1D,
    ComplexPDESolution1D,
    UniformGrid1D,
    compile_complex_pde_solution_scene,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SchrodingerProblem1D:
    """Finite-domain 1D time-dependent Schrödinger problem in SI units.

    Grid coordinates are meters, mass is a Quantity with mass dimension, time is
    seconds, and an optional potential function returns energy in joules.
    """

    grid: UniformGrid1D
    initial_values: tuple[complex, ...]
    mass: Quantity
    potential: RealFunction1D | None = None
    boundary: BoundaryMode1D = "fixed"
    initial_time: float = 0.0
    name: str = "schrodinger1d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("Schrodinger initial_values length must match grid")
        if self.mass.unit.dimension != MASS or self.mass.si_value <= 0.0:
            raise ValueError("Schrodinger particle mass must be a positive mass quantity")
        if self.potential is not None:
            if not self.potential.domain.contains(self.grid.start) or not self.potential.domain.contains(
                self.grid.end
            ):
                raise ValueError("Schrodinger potential domain must cover the spatial grid")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown Schrodinger boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("Schrodinger initial_time must be finite")
        if not self.name:
            raise ValueError("Schrodinger problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class SchrodingerSolution1D:
    pde_solution: ComplexPDESolution1D
    mass: Quantity
    boundary: BoundaryMode1D

    @property
    def grid(self) -> UniformGrid1D:
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


def probability_mass_1d(values: tuple[complex, ...], grid: UniformGrid1D) -> float:
    """Trapezoidal integral of |psi|^2 over the real spatial grid."""

    if len(values) != grid.count:
        raise ValueError("wavefunction sample count must match grid")
    densities = tuple(abs(complex(value)) ** 2 for value in values)
    weighted = 0.5 * densities[0] + sum(densities[1:-1]) + 0.5 * densities[-1]
    return float(weighted * grid.spacing)


def normalize_wavefunction_samples(
    values: tuple[complex, ...],
    grid: UniformGrid1D,
) -> tuple[complex, ...]:
    mass = probability_mass_1d(values, grid)
    if not math.isfinite(mass) or mass <= 0.0:
        raise ValueError("wavefunction samples have zero or invalid probability mass")
    factor = math.sqrt(mass)
    return tuple(complex(value) / factor for value in values)


def compile_schrodinger_solution_scene(solution: SchrodingerSolution1D):
    return compile_complex_pde_solution_scene(solution.pde_solution)


class SchrodingerDomain:
    """Quantum dynamics composed from typed constants and complex PDE capabilities."""

    name = "physics.quantum.schrodinger1d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.real_function1d"),
        DomainDependency("pde.complex.problem1d"),
        DomainDependency("pde.complex.second_derivative_1d"),
        DomainDependency("pde.complex.solve_method_of_lines"),
    )

    def register(self, registry: DomainRegistry) -> None:
        complex_problem_type = registry.require("pde.complex.problem1d")
        laplacian = registry.require("pde.complex.second_derivative_1d")
        solve_complex_pde = registry.require("pde.complex.solve_method_of_lines")
        hbar_si = REDUCED_PLANCK_CONSTANT.si_value

        def solve_schrodinger(
            problem: SchrodingerProblem1D,
            *,
            end_time: float,
            steps: int = 256,
            normalize_initial: bool = True,
        ) -> SchrodingerSolution1D:
            initial = tuple(complex(value) for value in problem.initial_values)
            if normalize_initial:
                initial = normalize_wavefunction_samples(initial, problem.grid)

            kinetic_coefficient = 1j * hbar_si / (2.0 * problem.mass.si_value)
            coordinates = problem.grid.coordinates

            def rhs(
                _time: float,
                grid: UniformGrid1D,
                values: tuple[complex, ...],
            ) -> tuple[complex, ...]:
                curvature = laplacian(values, grid, boundary=problem.boundary)
                result = []
                for index, (psi, second_derivative) in enumerate(
                    zip(values, curvature, strict=True)
                ):
                    derivative = kinetic_coefficient * second_derivative
                    if problem.potential is not None:
                        potential_joules = problem.potential.evaluate(coordinates[index])
                        derivative += (-1j * potential_joules / hbar_si) * psi
                    result.append(derivative)

                if problem.boundary == "fixed":
                    result[0] = 0.0j
                    result[-1] = 0.0j
                return tuple(result)

            pde_problem = complex_problem_type(
                grid=problem.grid,
                initial_values=initial,
                rhs=rhs,
                initial_time=problem.initial_time,
                name=problem.name,
            )
            pde_solution = solve_complex_pde(
                pde_problem,
                end_time=end_time,
                steps=steps,
            )
            return SchrodingerSolution1D(
                pde_solution=pde_solution,
                mass=problem.mass,
                boundary=problem.boundary,
            )

        registry.register_semantic_type(
            "physics.quantum.schrodinger1d.problem",
            SchrodingerProblem1D,
        )
        registry.register_semantic_type(
            "physics.quantum.schrodinger1d.solution",
            SchrodingerSolution1D,
        )
        registry.provide(
            "physics.quantum.schrodinger1d.problem",
            SchrodingerProblem1D,
        )
        registry.provide(
            "physics.quantum.schrodinger1d.solve",
            solve_schrodinger,
        )
        registry.provide(
            "physics.quantum.schrodinger1d.probability_mass",
            probability_mass_1d,
        )
        registry.register_visualization(
            SchrodingerSolution1D,
            compile_schrodinger_solution_scene,
        )
