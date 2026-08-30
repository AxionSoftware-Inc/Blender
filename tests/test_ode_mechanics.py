import pytest

from spectra.core.types import Vec3
from spectra.domains import DomainRegistry
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.physics.mechanics import MechanicsDomain, ParticleProblem
from spectra.domains.physics.mechanics_visualization import (
    compile_animated_trajectory_scene,
    compile_trajectory_scene,
)


def test_mechanics_uses_ode_domain_and_compiles_trajectory_scene() -> None:
    registry = DomainRegistry()
    registry.add_domains([MechanicsDomain(), DifferentialEquationsDomain()])
    solve_particle = registry.require("physics.mechanics.solve_particle")

    gravity = Vec3(0.0, -9.81, 0.0)

    problem = ParticleProblem.kilograms(
        2.0,
        initial_position=Vec3(0.0, 0.0, 0.0),
        initial_velocity=Vec3(10.0, 10.0, 0.0),
        force=lambda _t, _position, _velocity: gravity * 2.0,
        name="projectile",
    )
    trajectory = solve_particle(problem, end_time=1.0, steps=100)

    assert trajectory.positions[-1].x == pytest.approx(10.0, rel=1e-4)
    assert trajectory.positions[-1].y == pytest.approx(5.095, rel=1e-3)

    scene = compile_trajectory_scene(trajectory)
    assert [primitive.kind for primitive in scene.primitives] == ["polyline", "point", "point"]

    animated = compile_animated_trajectory_scene(trajectory)
    assert animated.timeline.duration == pytest.approx(1.0)
    midway = animated.sample(0.5)
    particle = midway.get("trajectory.particle")
    path = midway.get("trajectory.path")
    assert particle.position.x == pytest.approx(5.0, rel=1e-3)
    assert particle.position.y == pytest.approx(3.77375, rel=2e-3)
    assert path.trim_end == pytest.approx(0.5)
