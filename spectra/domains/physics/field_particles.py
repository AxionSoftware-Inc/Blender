from __future__ import annotations

from spectra.core.types import Vec3
from spectra.core.units import (
    ACCELERATION,
    CHARGE,
    ELECTRIC_FIELD,
    MAGNETIC_FIELD,
    MASS,
    Quantity,
)
from spectra.domains.mathematics.fields import (
    TimeDependentVectorField3D,
    VectorField3D,
)
from spectra.domains.physics.mechanics import ParticleProblem
from spectra.domains.registry import DomainDependency, DomainRegistry


Field3D = VectorField3D | TimeDependentVectorField3D


def _evaluate(field: Field3D, position: Vec3, time: float) -> Vec3:
    if isinstance(field, TimeDependentVectorField3D):
        return field.evaluate(position, time)
    return field.evaluate(position)


def _require_dimension(field: Field3D, dimension, label: str) -> None:
    if field.output_unit is None:
        raise ValueError(f"{label} requires an explicit physical output unit")
    if field.output_unit.dimension != dimension:
        raise ValueError(f"{label} field has incompatible physical dimension")


class FieldParticleDynamicsDomain:
    """Bridge renderer-neutral fields into the generic Newtonian particle solver."""

    name = "physics.field_particles"
    version = "1"
    dependencies = (
        DomainDependency("physics.mechanics.particle_problem"),
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("mathematics.time_vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        particle_type = registry.require("physics.mechanics.particle_problem")

        def in_acceleration_field(
            field: Field3D,
            *,
            mass: Quantity,
            initial_position: Vec3,
            initial_velocity: Vec3,
            initial_time: float = 0.0,
            name: str = "field_particle",
        ) -> ParticleProblem:
            if mass.unit.dimension != MASS or mass.si_value <= 0.0:
                raise ValueError("field particle mass must be a positive mass quantity")
            _require_dimension(field, ACCELERATION, "acceleration")
            mass_si = mass.si_value

            def force(time: float, position: Vec3, _velocity: Vec3) -> Vec3:
                return _evaluate(field, position, time) * mass_si

            return particle_type(
                mass=mass,
                initial_position=initial_position,
                initial_velocity=initial_velocity,
                force=force,
                initial_time=initial_time,
                name=name,
            )

        def in_electromagnetic_fields(
            electric_field: Field3D,
            magnetic_field: Field3D | None = None,
            *,
            charge: Quantity,
            mass: Quantity,
            initial_position: Vec3,
            initial_velocity: Vec3,
            initial_time: float = 0.0,
            name: str = "charged_particle",
        ) -> ParticleProblem:
            if charge.unit.dimension != CHARGE:
                raise ValueError("particle charge requires a charge quantity")
            if mass.unit.dimension != MASS or mass.si_value <= 0.0:
                raise ValueError("charged particle mass must be a positive mass quantity")
            _require_dimension(electric_field, ELECTRIC_FIELD, "electric")
            if magnetic_field is not None:
                _require_dimension(magnetic_field, MAGNETIC_FIELD, "magnetic")
            charge_si = charge.si_value

            def force(time: float, position: Vec3, velocity: Vec3) -> Vec3:
                electric = _evaluate(electric_field, position, time)
                magnetic_term = Vec3(0.0, 0.0, 0.0)
                if magnetic_field is not None:
                    magnetic = _evaluate(magnetic_field, position, time)
                    magnetic_term = velocity.cross(magnetic)
                return (electric + magnetic_term) * charge_si

            return particle_type(
                mass=mass,
                initial_position=initial_position,
                initial_velocity=initial_velocity,
                force=force,
                initial_time=initial_time,
                name=name,
            )

        registry.provide(
            "physics.field_particles.in_acceleration_field",
            in_acceleration_field,
        )
        registry.provide(
            "physics.field_particles.in_electromagnetic_fields",
            in_electromagnetic_fields,
        )
