import pytest

from spectra.core.types import Vec2, Vec3
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.field_dynamics import FieldDynamicsDomain, IntegralCurveProblem3D, PathlineProblem3D
from spectra.domains.field_dynamics.domain2d import FieldDynamics2DDomain, IntegralCurveProblem2D
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.mathematics.fields import TimeDependentVectorField3D, VectorField3D
from spectra.domains.mathematics.fields2d import VectorField2D
from spectra.domains.registry import DomainRegistry


def test_integral_curve_and_pathline_reuse_ode_solver() -> None:
    registry = DomainRegistry()
    registry.add_domains((FieldDynamicsDomain(), DifferentialEquationsDomain(), MathematicsDomain()))

    solve_curve = registry.require("field_dynamics.solve_integral_curve")
    solve_pathline = registry.require("field_dynamics.solve_pathline")

    curve = solve_curve(
        IntegralCurveProblem3D(
            VectorField3D(lambda _position: Vec3(2.0, 0.0, 0.0)),
            Vec3(0.0, 0.0, 0.0),
            mode="normalized",
        ),
        end_parameter=2.0,
        steps=32,
    )
    assert curve.positions[-1].x == pytest.approx(2.0, abs=1e-9)

    pathline = solve_pathline(
        PathlineProblem3D(
            TimeDependentVectorField3D(
                lambda _position, time: Vec3(time, 0.0, 0.0)
            ),
            Vec3(0.0, 0.0, 0.0),
        ),
        end_time=2.0,
        steps=64,
    )
    assert pathline.positions[-1].x == pytest.approx(2.0, rel=1e-5)


def test_2d_integral_curve_compiles_to_polyline() -> None:
    registry = DomainRegistry()
    registry.add_domains((FieldDynamics2DDomain(), DifferentialEquationsDomain(), MathematicsDomain()))
    solve = registry.require("field_dynamics.solve_integral_curve_2d")
    solution = solve(
        IntegralCurveProblem2D(
            VectorField2D(lambda _position: Vec2(1.0, 0.0)),
            Vec2(0.0, 1.0),
        ),
        end_parameter=1.0,
        steps=16,
    )
    scene = registry.compile_scene(solution)
    assert scene.primitives[0].points[-1].x == pytest.approx(1.0)
    assert scene.primitives[0].points[-1].y == pytest.approx(1.0)
