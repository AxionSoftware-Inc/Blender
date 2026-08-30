import pytest

from spectra.core.types import Vec3
from spectra.core.units import JOULE, KILOGRAM, METER_PER_SECOND_SQUARED, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import ScalarField3D, VectorField3D
from spectra.domains.potential_fields import PotentialField3D


def test_uniform_gravity_total_energy_is_conserved_by_mechanics_composition() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.field_particles", "physics.potential_energy"],
    )

    mass = Quantity(2.0, KILOGRAM)
    gravity = VectorField3D(
        lambda _position: Vec3(0.0, 0.0, -9.81),
        name="uniform_gravity",
        output_unit=METER_PER_SECOND_SQUARED,
    )
    potential = ScalarField3D(
        lambda position: 9.81 * position.z,
        name="uniform_gravity_potential",
        output_unit=JOULE / KILOGRAM,
    )
    model = PotentialField3D(potential=potential, field=gravity, name="uniform_gravity")

    problem = registry.require("physics.field_particles.in_acceleration_field")(
        gravity,
        mass=mass,
        initial_position=Vec3(0.0, 0.0, 10.0),
        initial_velocity=Vec3(0.0, 0.0, 0.0),
    )
    trajectory = registry.require("physics.mechanics.solve_particle")(
        problem,
        end_time=1.0,
        steps=32,
    )
    history = registry.require("physics.potential_energy.compute_history")(
        trajectory,
        model,
        mass=mass,
        coupling=mass,
    )

    assert history.total_joules[0] == pytest.approx(196.2, abs=1e-9)
    assert history.total_joules[-1] == pytest.approx(196.2, abs=1e-8)
    assert history.relative_total_drift < 1e-9


def test_energy_diagnostics_reject_dimensionally_invalid_coupling() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.potential_energy"])

    trajectory_type = registry.require("physics.mechanics.trajectory", min_version=2)
    trajectory = trajectory_type(
        times=(0.0,),
        positions=(Vec3(0.0, 0.0, 0.0),),
        velocities=(Vec3(0.0, 0.0, 0.0),),
    )
    model = PotentialField3D(
        potential=ScalarField3D(
            lambda _position: 1.0,
            output_unit=JOULE / KILOGRAM,
        ),
        field=VectorField3D(
            lambda _position: Vec3(0.0, 0.0, 0.0),
            output_unit=METER_PER_SECOND_SQUARED,
        ),
    )

    with pytest.raises(ValueError):
        registry.require("physics.potential_energy.compute_history")(
            trajectory,
            model,
            mass=Quantity(1.0, KILOGRAM),
            coupling=Quantity(1.0, JOULE),
        )
