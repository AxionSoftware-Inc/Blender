from __future__ import annotations

from spectra.domains import DomainRegistry
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.mathematics import Function1D, Interval, MathematicsDomain
from spectra.domains.physics import MechanicsDomain, ParticleProblem
from spectra.domains.probability import DiscreteDistribution, ProbabilityDomain
from spectra.core.types import Vec3


def test_registry_compiles_semantics_without_domain_specific_calls() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        [
            MechanicsDomain(),
            DifferentialEquationsDomain(),
            ProbabilityDomain(),
            MathematicsDomain(),
        ]
    )

    function = Function1D.from_expression("x*x", Interval(-1.0, 1.0))
    function_scene = registry.compile_scene(function)
    assert function_scene.get("function") is not None

    distribution = DiscreteDistribution.from_pairs(((0.0, 0.25), (1.0, 0.75)))
    distribution_scene = registry.compile_scene(distribution)
    assert len(distribution_scene.primitives) == 4

    solve_particle = registry.require("physics.mechanics.solve_particle")
    problem = ParticleProblem.kilograms(
        1.0,
        Vec3(0.0, 0.0, 0.0),
        Vec3(1.0, 0.0, 0.0),
        lambda _t, _position, _velocity: Vec3(0.0, 0.0, 0.0),
    )
    trajectory = solve_particle(problem, end_time=1.0, steps=4)
    trajectory_scene = registry.compile_scene(trajectory)
    assert trajectory_scene.get("trajectory.path") is not None


def test_registry_reports_visualization_support() -> None:
    registry = DomainRegistry()
    registry.add_domain(ProbabilityDomain())
    distribution = DiscreteDistribution.from_pairs(((1.0, 1.0),))

    assert registry.can_visualize(distribution)
    assert registry.can_visualize(DiscreteDistribution)
    assert not registry.can_visualize(object())
