import pytest

from spectra.core.types import Vec3
from spectra.core.units import COULOMB, KILOGRAM, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.maxwell3d import MaxwellProblem3D


def test_uniform_maxwell_electric_field_drives_particle_through_existing_mechanics_solver() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["physics.electromagnetism.maxwell_particles3d"])

    axis = UniformGrid1D(0.0, 1.0, 3)
    grid = UniformGrid3D(axis, axis, axis)
    electric = (Vec3(2.0, 0.0, 0.0),) * grid.count
    magnetic = (Vec3(0.0, 0.0, 0.0),) * grid.count
    maxwell = registry.require("physics.maxwell.solve3d")(
        MaxwellProblem3D(
            grid=grid,
            initial_electric=electric,
            initial_magnetic=magnetic,
            boundary="periodic",
            name="uniform_electric",
        ),
        end_time=1.0,
        steps=4,
    )

    particle_problem = registry.require(
        "physics.maxwell.particle_problem_from_solution3d"
    )(
        maxwell,
        charge=Quantity(1.0, COULOMB),
        mass=Quantity(1.0, KILOGRAM),
        initial_position=Vec3(0.0, 0.0, 0.0),
        initial_velocity=Vec3(0.0, 0.0, 0.0),
    )
    trajectory = registry.require("physics.mechanics.solve_particle")(
        particle_problem,
        end_time=1.0,
        steps=16,
    )

    assert trajectory.velocities[-1].x == pytest.approx(2.0, rel=1e-8)
    assert trajectory.positions[-1].x == pytest.approx(1.0, rel=1e-8)
    assert trajectory.positions[-1].y == pytest.approx(0.0, abs=1e-12)
    assert trajectory.positions[-1].z == pytest.approx(0.0, abs=1e-12)
