from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import MASS, KILOGRAM, Quantity
from spectra.domains.registry import DomainDependency, DomainRegistry


ForceFunction = Callable[[float, Vec3, Vec3], Vec3]


@dataclass(frozen=True, slots=True)
class ParticleProblem:
    mass: Quantity
    initial_position: Vec3
    initial_velocity: Vec3
    force: ForceFunction
    initial_time: float = 0.0
    name: str = "particle"

    def __post_init__(self) -> None:
        if self.mass.unit.dimension != MASS:
            raise ValueError("particle mass requires a mass quantity")
        if self.mass.si_value <= 0.0:
            raise ValueError("particle mass must be positive")
        if not math.isfinite(self.initial_time):
            raise ValueError("particle initial_time must be finite")

    @classmethod
    def kilograms(
        cls,
        mass: float,
        initial_position: Vec3,
        initial_velocity: Vec3,
        force: ForceFunction,
        *,
        initial_time: float = 0.0,
        name: str = "particle",
    ) -> "ParticleProblem":
        return cls(
            mass=Quantity(mass, KILOGRAM),
            initial_position=initial_position,
            initial_velocity=initial_velocity,
            force=force,
            initial_time=initial_time,
            name=name,
        )


@dataclass(frozen=True, slots=True)
class Trajectory:
    times: tuple[float, ...]
    positions: tuple[Vec3, ...]
    velocities: tuple[Vec3, ...]
    name: str = "trajectory"

    def __post_init__(self) -> None:
        if not self.times:
            raise ValueError("trajectory cannot be empty")
        if not (len(self.times) == len(self.positions) == len(self.velocities)):
            raise ValueError("trajectory arrays must have equal lengths")
        if any(not math.isfinite(time) for time in self.times):
            raise ValueError("trajectory times must be finite")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("trajectory times must be strictly increasing")


class MechanicsDomain:
    name = "mechanics"
    version = "3"
    dependencies = (
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.physics.mechanics_visualization import compile_trajectory_scene

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)

        def solve_particle(
            problem: ParticleProblem,
            *,
            end_time: float,
            steps: int = 256,
        ) -> Trajectory:
            mass = problem.mass.si_value

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != 6:
                    raise ValueError("mechanics particle state must have 6 components")
                position = Vec3(state[0], state[1], state[2])
                velocity = Vec3(state[3], state[4], state[5])
                acceleration = problem.force(time, position, velocity) * (1.0 / mass)
                return (
                    velocity.x,
                    velocity.y,
                    velocity.z,
                    acceleration.x,
                    acceleration.y,
                    acceleration.z,
                )

            initial = (
                problem.initial_position.x,
                problem.initial_position.y,
                problem.initial_position.z,
                problem.initial_velocity.x,
                problem.initial_velocity.y,
                problem.initial_velocity.z,
            )
            solution = solve_ode(
                system_type(derivative, problem.initial_time, initial, name=problem.name),
                end_time=end_time,
                steps=steps,
            )
            positions = tuple(Vec3(state[0], state[1], state[2]) for state in solution.states)
            velocities = tuple(Vec3(state[3], state[4], state[5]) for state in solution.states)
            return Trajectory(solution.times, positions, velocities, name=problem.name)

        registry.register_semantic_type("physics.mechanics.particle_problem", ParticleProblem)
        registry.register_semantic_type("physics.mechanics.trajectory", Trajectory)
        registry.provide("physics.mechanics.particle_problem", ParticleProblem)
        registry.provide("physics.mechanics.trajectory", Trajectory, version=2)
        registry.provide("physics.mechanics.solve_particle", solve_particle, version=2)
        registry.register_visualization(Trajectory, compile_trajectory_scene)
