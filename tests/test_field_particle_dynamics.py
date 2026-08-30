import pytest

from spectra.core.types import Vec3
from spectra.core.units import (
    COULOMB,
    KILOGRAM,
    METER_PER_SECOND_SQUARED,
    NEWTON_PER_COULOMB,
    Quantity,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import VectorField3D


def test_acceleration_field_reuses_mechanics_solver() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.field_particles"])

    gravity = VectorField3D(
        lambda _position: Vec3(0.0, 0.0, -9.81),
        name="uniform_gravity",
        output_unit=METER_PER_SECOND_SQUARED,
    )
    problem = registry.require("physics.field_particles.in_acceleration_field")(
        gravity,
        mass=Quantity(2.0, KILOGRAM),
        initial_position=Vec3(0.0, 0.0, 0.0),
        initial_velocity=Vec3(0.0, 0.0, 0.0),
    )
    trajectory = registry.require("physics.mechanics.solve_particle")(
        problem,
        end_time=1.0,
        steps=32,
    )

    assert trajectory.positions[-1].z == pytest.approx(-4.905, rel=1e-9, abs=1e-9)
    assert trajectory.velocities[-1].z == pytest.approx(-9.81, rel=1e-9, abs=1e-9)


def test_uniform_electric_field_composes_lorentz_force_with_mechanics() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.field_particles"])

    electric = VectorField3D(
        lambda _position: Vec3(1.0, 0.0, 0.0),
        name="uniform_electric",
        output_unit=NEWTON_PER_COULOMB,
    )
    problem = registry.require("physics.field_particles.in_electromagnetic_fields")(
        electric,
        charge=Quantity(2.0, COULOMB),
        mass=Quantity(1.0, KILOGRAM),
        initial_position=Vec3(0.0, 0.0, 0.0),
        initial_velocity=Vec3(0.0, 0.0, 0.0),
    )
    trajectory = registry.require("physics.mechanics.solve_particle")(
        problem,
        end_time=1.0,
        steps=32,
    )

    assert trajectory.positions[-1].x == pytest.approx(1.0, rel=1e-9, abs=1e-9)
    assert trajectory.velocities[-1].x == pytest.approx(2.0, rel=1e-9, abs=1e-9)
