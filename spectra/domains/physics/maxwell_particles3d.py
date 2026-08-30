from __future__ import annotations

from spectra.core.types import Vec3
from spectra.core.units import Quantity
from spectra.domains.physics.maxwell3d import MaxwellSolution3D
from spectra.domains.physics.mechanics import ParticleProblem
from spectra.domains.registry import DomainDependency, DomainRegistry


class MaxwellParticleDynamics3DDomain:
    """Compose sampled Maxwell fields with the generic Lorentz-force particle bridge."""

    name = "physics.electromagnetism.maxwell_particles3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.maxwell.solution3d"),
        DomainDependency("physics.maxwell.fields_from_solution3d"),
        DomainDependency(
            "physics.field_particles.in_electromagnetic_fields",
            min_version=2,
        ),
    )

    def register(self, registry: DomainRegistry) -> None:
        fields_from_solution = registry.require("physics.maxwell.fields_from_solution3d")
        in_electromagnetic_fields = registry.require(
            "physics.field_particles.in_electromagnetic_fields",
            min_version=2,
        )

        def particle_problem_from_solution(
            solution: MaxwellSolution3D,
            *,
            charge: Quantity,
            mass: Quantity,
            initial_position: Vec3,
            initial_velocity: Vec3,
            initial_time: float | None = None,
            name: str = "maxwell_charged_particle",
        ) -> ParticleProblem:
            fields = fields_from_solution(solution)
            start = fields.start_time if initial_time is None else float(initial_time)
            if start < fields.start_time or start > fields.end_time:
                raise ValueError("charged-particle initial_time must lie inside Maxwell history")
            return in_electromagnetic_fields(
                fields.electric,
                fields.magnetic,
                charge=charge,
                mass=mass,
                initial_position=initial_position,
                initial_velocity=initial_velocity,
                initial_time=start,
                name=name,
            )

        registry.provide(
            "physics.maxwell.particle_problem_from_solution3d",
            particle_problem_from_solution,
        )
