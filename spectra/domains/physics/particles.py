from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spectra.core.types import Color, Vec3
from spectra.core.units import KILOGRAM, MASS, Quantity
from spectra.domains.registry import DomainDependency, DomainRegistry


ManyBodyForceFunction = Callable[
    [float, tuple[Vec3, ...], tuple[Vec3, ...]],
    tuple[Vec3, ...],
]


@dataclass(frozen=True, slots=True)
class Particle:
    mass: Quantity
    position: Vec3
    velocity: Vec3 = Vec3(0.0, 0.0, 0.0)
    radius: float = 0.05
    color: Color = Color(0.65, 0.85, 1.0, 1.0)

    def __post_init__(self) -> None:
        if self.mass.unit.dimension != MASS:
            raise ValueError("particle mass requires a mass quantity")
        if self.mass.si_value <= 0.0:
            raise ValueError("particle mass must be positive")
        if self.radius < 0.0:
            raise ValueError("particle radius cannot be negative")

    @classmethod
    def kilograms(
        cls,
        mass: float,
        position: Vec3,
        velocity: Vec3 = Vec3(0.0, 0.0, 0.0),
        *,
        radius: float = 0.05,
        color: Color = Color(0.65, 0.85, 1.0, 1.0),
    ) -> "Particle":
        return cls(Quantity(mass, KILOGRAM), position, velocity, radius, color)


@dataclass(frozen=True, slots=True)
class ParticleSystemProblem:
    particles: tuple[Particle, ...]
    force: ManyBodyForceFunction
    initial_time: float = 0.0
    name: str = "particle_system"

    def __post_init__(self) -> None:
        if not self.particles:
            raise ValueError("particle system requires at least one particle")


@dataclass(frozen=True, slots=True)
class ParticleSystemTrajectory:
    times: tuple[float, ...]
    positions: tuple[tuple[Vec3, ...], ...]
    velocities: tuple[tuple[Vec3, ...], ...]
    radii: tuple[float, ...]
    colors: tuple[Color, ...]
    name: str = "particle_system"

    def __post_init__(self) -> None:
        if not self.times:
            raise ValueError("particle-system trajectory cannot be empty")
        if not (len(self.times) == len(self.positions) == len(self.velocities)):
            raise ValueError("particle-system trajectory frame counts must match")
        particle_count = len(self.radii)
        if particle_count == 0 or len(self.colors) != particle_count:
            raise ValueError("particle-system visual arrays must be non-empty and equal")
        for positions, velocities in zip(self.positions, self.velocities, strict=True):
            if len(positions) != particle_count or len(velocities) != particle_count:
                raise ValueError("particle-system trajectory particle count changed over time")

    @property
    def particle_count(self) -> int:
        return len(self.radii)


class ParticleSystemsDomain:
    name = "physics.particles"
    version = "1"
    dependencies = (
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.physics.particles_visualization import compile_particle_system_scene

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_system(
            problem: ParticleSystemProblem,
            *,
            end_time: float,
            steps: int = 256,
        ) -> ParticleSystemTrajectory:
            particle_count = len(problem.particles)
            masses = tuple(particle.mass.si_value for particle in problem.particles)

            initial_position_values = tuple(
                component
                for particle in problem.particles
                for component in (particle.position.x, particle.position.y, particle.position.z)
            )
            initial_velocity_values = tuple(
                component
                for particle in problem.particles
                for component in (particle.velocity.x, particle.velocity.y, particle.velocity.z)
            )
            initial_state = initial_position_values + initial_velocity_values

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                expected = particle_count * 6
                if len(state) != expected:
                    raise ValueError("particle-system ODE state has invalid dimension")

                split = particle_count * 3
                positions_raw = state[:split]
                velocities_raw = state[split:]
                positions = tuple(
                    Vec3(*positions_raw[index : index + 3])
                    for index in range(0, split, 3)
                )
                velocities = tuple(
                    Vec3(*velocities_raw[index : index + 3])
                    for index in range(0, split, 3)
                )
                forces = tuple(problem.force(time, positions, velocities))
                if len(forces) != particle_count:
                    raise ValueError("particle-system force function returned wrong particle count")
                accelerations = tuple(
                    force * (1.0 / mass)
                    for force, mass in zip(forces, masses, strict=True)
                )
                return tuple(
                    component
                    for velocity in velocities
                    for component in (velocity.x, velocity.y, velocity.z)
                ) + tuple(
                    component
                    for acceleration in accelerations
                    for component in (acceleration.x, acceleration.y, acceleration.z)
                )

            solution = solve_ode(
                system_type(
                    derivative,
                    problem.initial_time,
                    initial_state,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )

            positions_by_time: list[tuple[Vec3, ...]] = []
            velocities_by_time: list[tuple[Vec3, ...]] = []
            split = particle_count * 3
            for state in solution.states:
                positions_raw = state[:split]
                velocities_raw = state[split:]
                positions_by_time.append(
                    tuple(
                        Vec3(*positions_raw[index : index + 3])
                        for index in range(0, split, 3)
                    )
                )
                velocities_by_time.append(
                    tuple(
                        Vec3(*velocities_raw[index : index + 3])
                        for index in range(0, split, 3)
                    )
                )

            trajectory = ParticleSystemTrajectory(
                times=solution.times,
                positions=tuple(positions_by_time),
                velocities=tuple(velocities_by_time),
                radii=tuple(particle.radius for particle in problem.particles),
                colors=tuple(particle.color for particle in problem.particles),
                name=problem.name,
            )
            return trajectory

        registry.register_semantic_type("physics.particles.particle", Particle)
        registry.register_semantic_type("physics.particles.problem", ParticleSystemProblem)
        registry.register_semantic_type("physics.particles.trajectory", ParticleSystemTrajectory)
        registry.provide("physics.particles.particle", Particle, version=1)
        registry.provide("physics.particles.solve_system", solve_system, version=1)
        registry.register_visualization(ParticleSystemTrajectory, compile_particle_system_scene)
