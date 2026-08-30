from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import FREQUENCY, HERTZ, VELOCITY, Quantity
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.partial_differential_equations.second_order3d import (
    SecondOrderScalarPDEProblem3D,
    SecondOrderScalarPDESolution3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class WaveEquationProblem3D:
    grid: UniformGrid3D
    initial_displacement: tuple[float, ...]
    initial_velocity: tuple[float, ...]
    wave_speed: Quantity
    damping: Quantity = Quantity(0.0, HERTZ)
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "wave_equation3d"

    def __post_init__(self) -> None:
        if len(self.initial_displacement) != self.grid.count:
            raise ValueError("3D wave displacement sample count must match grid")
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("3D wave velocity sample count must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_displacement):
            raise ValueError("3D wave displacement samples must be finite")
        if not all(math.isfinite(float(value)) for value in self.initial_velocity):
            raise ValueError("3D wave velocity samples must be finite")
        if self.wave_speed.unit.dimension != VELOCITY or self.wave_speed.si_value <= 0.0:
            raise ValueError("3D wave speed must be a positive velocity quantity")
        if self.damping.unit.dimension != FREQUENCY or self.damping.si_value < 0.0:
            raise ValueError("3D wave damping must be a non-negative frequency quantity")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D wave boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D wave initial_time must be finite")
        if not self.name:
            raise ValueError("3D wave equation name cannot be empty")


@dataclass(frozen=True, slots=True)
class WaveEquationSolution3D:
    pde_solution: SecondOrderScalarPDESolution3D
    wave_speed_si: float
    damping_si: float
    boundary: BoundaryMode3D

    @property
    def grid(self) -> UniformGrid3D:
        return self.pde_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.pde_solution.times

    @property
    def displacements(self) -> tuple[tuple[float, ...], ...]:
        return self.pde_solution.values

    @property
    def velocities(self) -> tuple[tuple[float, ...], ...]:
        return self.pde_solution.velocities

    @property
    def duration(self) -> float:
        return self.pde_solution.duration

    @property
    def name(self) -> str:
        return self.pde_solution.name


class WaveEquation3DDomain:
    name = "physics.wave_equation.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.second_order_problem3d"),
        DomainDependency("pde.solve_second_order_3d"),
        DomainDependency("pde.laplacian_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        problem_type = registry.require("pde.second_order_problem3d")
        solve_second_order = registry.require("pde.solve_second_order_3d")
        laplacian = registry.require("pde.laplacian_3d")

        def solve_wave(
            problem: WaveEquationProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> WaveEquationSolution3D:
            speed_squared = problem.wave_speed.si_value ** 2
            damping_rate = problem.damping.si_value

            def acceleration(
                _time: float,
                grid: UniformGrid3D,
                values: tuple[float, ...],
                velocities: tuple[float, ...],
            ) -> tuple[float, ...]:
                curvature = laplacian(values, grid, boundary=problem.boundary)
                return tuple(
                    speed_squared * lap - damping_rate * velocity
                    for lap, velocity in zip(curvature, velocities, strict=True)
                )

            pde_solution = solve_second_order(
                problem_type(
                    grid=problem.grid,
                    initial_values=tuple(float(value) for value in problem.initial_displacement),
                    initial_velocity=tuple(float(value) for value in problem.initial_velocity),
                    acceleration_rhs=acceleration,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return WaveEquationSolution3D(
                pde_solution=pde_solution,
                wave_speed_si=problem.wave_speed.si_value,
                damping_si=damping_rate,
                boundary=problem.boundary,
            )

        registry.register_semantic_type(
            "physics.wave_equation.problem3d",
            WaveEquationProblem3D,
        )
        registry.register_semantic_type(
            "physics.wave_equation.solution3d",
            WaveEquationSolution3D,
        )
        registry.provide("physics.wave_equation.problem3d", WaveEquationProblem3D)
        registry.provide("physics.wave_equation.solution3d", WaveEquationSolution3D)
        registry.provide("physics.wave_equation.solve3d", solve_wave)
