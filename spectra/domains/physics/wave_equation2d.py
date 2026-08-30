from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import FREQUENCY, HERTZ, VELOCITY, Quantity
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.partial_differential_equations.second_order2d import (
    SecondOrderScalarPDEProblem2D,
    SecondOrderScalarPDESolution2D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class WaveEquationProblem2D:
    grid: UniformGrid2D
    initial_displacement: tuple[float, ...]
    initial_velocity: tuple[float, ...]
    wave_speed: Quantity
    damping: Quantity = Quantity(0.0, HERTZ)
    boundary: BoundaryMode2D = "fixed"
    initial_time: float = 0.0
    name: str = "wave_equation2d"

    def __post_init__(self) -> None:
        if len(self.initial_displacement) != self.grid.count:
            raise ValueError("wave displacement sample count must match grid")
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("wave velocity sample count must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_displacement):
            raise ValueError("wave displacement samples must be finite")
        if not all(math.isfinite(float(value)) for value in self.initial_velocity):
            raise ValueError("wave velocity samples must be finite")
        if self.wave_speed.unit.dimension != VELOCITY or self.wave_speed.si_value <= 0.0:
            raise ValueError("wave speed must be a positive velocity quantity")
        if self.damping.unit.dimension != FREQUENCY or self.damping.si_value < 0.0:
            raise ValueError("wave damping must be a non-negative frequency quantity")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown wave boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("wave initial_time must be finite")
        if not self.name:
            raise ValueError("wave equation name cannot be empty")


@dataclass(frozen=True, slots=True)
class WaveEquationSolution2D:
    pde_solution: SecondOrderScalarPDESolution2D
    wave_speed_si: float
    damping_si: float
    boundary: BoundaryMode2D

    @property
    def grid(self) -> UniformGrid2D:
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


class WaveEquation2DDomain:
    name = "physics.wave_equation.2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.second_order_problem2d"),
        DomainDependency("pde.solve_second_order_2d"),
        DomainDependency("pde.laplacian_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization2d import (
            compile_scalar_pde_solution_2d_scene,
        )

        problem_type = registry.require("pde.second_order_problem2d")
        solve_second_order = registry.require("pde.solve_second_order_2d")
        laplacian = registry.require("pde.laplacian_2d")

        def solve_wave(
            problem: WaveEquationProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> WaveEquationSolution2D:
            speed_squared = problem.wave_speed.si_value ** 2
            damping_rate = problem.damping.si_value

            def acceleration(
                _time: float,
                grid: UniformGrid2D,
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
            return WaveEquationSolution2D(
                pde_solution=pde_solution,
                wave_speed_si=problem.wave_speed.si_value,
                damping_si=damping_rate,
                boundary=problem.boundary,
            )

        def compile_solution(solution: WaveEquationSolution2D):
            return compile_scalar_pde_solution_2d_scene(
                solution.pde_solution.value_solution()
            )

        registry.register_semantic_type(
            "physics.wave_equation.problem2d",
            WaveEquationProblem2D,
        )
        registry.register_semantic_type(
            "physics.wave_equation.solution2d",
            WaveEquationSolution2D,
        )
        registry.provide("physics.wave_equation.problem2d", WaveEquationProblem2D)
        registry.provide("physics.wave_equation.solve2d", solve_wave)
        registry.register_visualization(WaveEquationSolution2D, compile_solution)
