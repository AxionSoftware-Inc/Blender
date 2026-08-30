import pytest

from spectra.core.primitives import PointCloud
from spectra.core.types import Color, Vec3
from spectra.domains import DomainRegistry
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.physics import Particle, ParticleSystemProblem, ParticleSystemsDomain


def test_particle_system_reuses_ode_and_animates_one_point_cloud() -> None:
    registry = DomainRegistry()
    registry.add_domains([ParticleSystemsDomain(), DifferentialEquationsDomain()])
    solve_system = registry.require("physics.particles.solve_system")

    particles = (
        Particle.kilograms(
            1.0,
            Vec3(0.0, 0.0, 0.0),
            Vec3(1.0, 0.0, 0.0),
            radius=0.1,
            color=Color(1.0, 0.2, 0.2, 1.0),
        ),
        Particle.kilograms(
            2.0,
            Vec3(0.0, 1.0, 0.0),
            Vec3(0.0, 2.0, 0.0),
            radius=0.2,
            color=Color(0.2, 0.6, 1.0, 1.0),
        ),
    )
    problem = ParticleSystemProblem(
        particles=particles,
        force=lambda _t, positions, _velocities: tuple(
            Vec3(0.0, 0.0, 0.0) for _ in positions
        ),
        name="free-particles",
    )
    trajectory = solve_system(problem, end_time=1.0, steps=10)

    assert trajectory.particle_count == 2
    assert trajectory.positions[-1][0].x == pytest.approx(1.0)
    assert trajectory.positions[-1][0].y == pytest.approx(0.0)
    assert trajectory.positions[-1][1].x == pytest.approx(0.0)
    assert trajectory.positions[-1][1].y == pytest.approx(3.0)

    scene = registry.compile_scene(trajectory)
    assert len(scene.primitives) == 1
    cloud = scene.primitives[0]
    assert isinstance(cloud, PointCloud)
    assert cloud.instance_count == 2
    assert scene.timeline.duration == pytest.approx(1.0)

    halfway = scene.sample(0.5)
    halfway_cloud = halfway.get("free-particles.particles")
    assert isinstance(halfway_cloud, PointCloud)
    assert halfway_cloud.positions[0].x == pytest.approx(0.5)
    assert halfway_cloud.positions[1].y == pytest.approx(2.0)


def test_particle_system_force_count_is_validated() -> None:
    registry = DomainRegistry()
    registry.add_domains([ParticleSystemsDomain(), DifferentialEquationsDomain()])
    solve_system = registry.require("physics.particles.solve_system")

    problem = ParticleSystemProblem(
        particles=(Particle.kilograms(1.0, Vec3(0.0, 0.0, 0.0)),),
        force=lambda _t, _positions, _velocities: (),
    )
    with pytest.raises(ValueError, match="wrong particle count"):
        solve_system(problem, end_time=0.1, steps=1)
