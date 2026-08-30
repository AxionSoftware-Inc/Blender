from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import FREQUENCY, HERTZ, PASCAL, VELOCITY, Quantity, Unit
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.physics.wave_equation3d import WaveEquationSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class AcousticPressureProblem3D:
    """Linear scalar acoustic-pressure propagation on a regular 3D grid."""

    grid: UniformGrid3D
    initial_pressure: tuple[float, ...]
    initial_pressure_rate: tuple[float, ...]
    sound_speed: Quantity
    damping: Quantity = Quantity(0.0, HERTZ)
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "acoustic_pressure3d"

    def __post_init__(self) -> None:
        if len(self.initial_pressure) != self.grid.count:
            raise ValueError("acoustic pressure sample count must match grid")
        if len(self.initial_pressure_rate) != self.grid.count:
            raise ValueError("acoustic pressure-rate sample count must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_pressure):
            raise ValueError("acoustic pressure samples must be finite")
        if not all(math.isfinite(float(value)) for value in self.initial_pressure_rate):
            raise ValueError("acoustic pressure-rate samples must be finite")
        if self.sound_speed.unit.dimension != VELOCITY or self.sound_speed.si_value <= 0.0:
            raise ValueError("sound speed must be a positive velocity quantity")
        if self.damping.unit.dimension != FREQUENCY or self.damping.si_value < 0.0:
            raise ValueError("acoustic damping must be a non-negative frequency quantity")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown acoustic boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("acoustic initial_time must be finite")
        if not self.name:
            raise ValueError("acoustic problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class AcousticPressureSolution3D:
    wave_solution: WaveEquationSolution3D
    pressure_unit: Unit = PASCAL

    @property
    def grid(self) -> UniformGrid3D:
        return self.wave_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.wave_solution.times

    @property
    def pressure_states(self) -> tuple[tuple[float, ...], ...]:
        return self.wave_solution.displacements

    @property
    def pressure_rate_states(self) -> tuple[tuple[float, ...], ...]:
        return self.wave_solution.velocities

    @property
    def duration(self) -> float:
        return self.wave_solution.duration

    @property
    def name(self) -> str:
        return self.wave_solution.name


class Acoustics3DDomain:
    """Linear acoustics as a physics semantic layer over the generic 3D wave solver."""

    name = "physics.acoustics.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.wave_equation.problem3d"),
        DomainDependency("physics.wave_equation.solve3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        wave_problem_type = registry.require("physics.wave_equation.problem3d")
        solve_wave = registry.require("physics.wave_equation.solve3d")

        def solve_acoustics(
            problem: AcousticPressureProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> AcousticPressureSolution3D:
            wave_solution = solve_wave(
                wave_problem_type(
                    grid=problem.grid,
                    initial_displacement=tuple(float(value) for value in problem.initial_pressure),
                    initial_velocity=tuple(float(value) for value in problem.initial_pressure_rate),
                    wave_speed=problem.sound_speed,
                    damping=problem.damping,
                    boundary=problem.boundary,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return AcousticPressureSolution3D(wave_solution=wave_solution)

        registry.register_semantic_type("physics.acoustics.problem3d", AcousticPressureProblem3D)
        registry.register_semantic_type("physics.acoustics.solution3d", AcousticPressureSolution3D)
        registry.provide("physics.acoustics.problem3d", AcousticPressureProblem3D)
        registry.provide("physics.acoustics.solution3d", AcousticPressureSolution3D)
        registry.provide("physics.acoustics.solve3d", solve_acoustics)
