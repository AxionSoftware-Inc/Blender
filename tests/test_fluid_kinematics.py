import pytest

from spectra.core.types import Vec2
from spectra.domains.calculus.vector2d import VectorCalculus2DDomain
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.field_dynamics.domain2d import FieldDynamics2DDomain
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.mathematics.fields2d import ScalarField2D, VectorField2D
from spectra.domains.physics.fluid_kinematics import FluidKinematics2DDomain, SteadyFlow2D
from spectra.domains.registry import DomainRegistry


def test_vector_calculus_2d_vortex_field() -> None:
    registry = DomainRegistry()
    registry.add_domains((VectorCalculus2DDomain(), MathematicsDomain()))
    gradient = registry.require("calculus.gradient_at_2d")
    divergence = registry.require("calculus.divergence_at_2d")
    curl = registry.require("calculus.scalar_curl_at_2d")

    scalar = ScalarField2D(lambda point: point.x * point.x + point.y * point.y)
    vortex = VectorField2D(lambda point: Vec2(-point.y, point.x))
    position = Vec2(2.0, -3.0)

    value = gradient(scalar, position)
    assert value.x == pytest.approx(4.0, rel=1e-5)
    assert value.y == pytest.approx(-6.0, rel=1e-5)
    assert divergence(vortex, position) == pytest.approx(0.0, abs=1e-8)
    assert curl(vortex, position) == pytest.approx(2.0, rel=1e-5)


def test_fluid_kinematics_builds_streamline_problem() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        (
            FluidKinematics2DDomain(),
            FieldDynamics2DDomain(),
            VectorCalculus2DDomain(),
            DifferentialEquationsDomain(),
            MathematicsDomain(),
        )
    )
    flow = SteadyFlow2D(VectorField2D(lambda point: Vec2(-point.y, point.x)))
    position = Vec2(1.0, 0.0)

    assert registry.require("physics.fluid.speed_at")(flow, position) == pytest.approx(1.0)
    assert registry.require("physics.fluid.divergence_at")(flow, position) == pytest.approx(0.0, abs=1e-8)
    assert registry.require("physics.fluid.vorticity_at")(flow, position) == pytest.approx(2.0, rel=1e-5)
    assert registry.require("physics.fluid.is_locally_incompressible")(flow, position)

    problem = registry.require("physics.fluid.streamline_problem")(flow, position)
    assert problem.field is flow.velocity
