import pytest

from spectra.core.primitives import Group, Polyline
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import VectorField3D


def test_bidirectional_bundle_spans_both_sides_of_seed() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["field_dynamics.bundles3d"])

    problem_type = registry.require("field_dynamics.integral_curve_bundle_problem3d")
    solve = registry.require("field_dynamics.solve_integral_curve_bundle3d")
    field = VectorField3D(lambda _position: Vec3(2.0, 0.0, 0.0), name="uniform")

    solution = solve(
        problem_type(
            field=field,
            seeds=(Vec3(0.0, 0.0, 0.0),),
            parameter_length=1.0,
            steps_per_direction=16,
            mode="normalized",
            bidirectional=True,
            name="uniform_lines",
        )
    )

    curve = solution.curves[0]
    assert curve.positions[0].x == pytest.approx(-1.0, abs=1e-9)
    assert curve.positions[-1].x == pytest.approx(1.0, abs=1e-9)
    assert curve.positions[len(curve.positions) // 2] == Vec3(0.0, 0.0, 0.0)

    scene = registry.compile_scene(solution)
    polylines = tuple(item for item in scene.primitives if isinstance(item, Polyline))
    groups = tuple(item for item in scene.primitives if isinstance(item, Group))
    assert len(polylines) == 1
    assert len(groups) == 1
    assert groups[0].children == (polylines[0].id,)


def test_bundle_catalog_auto_loads_ode_and_field_dependencies() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["field_dynamics.bundles3d"])

    assert "mathematics" in loaded
    assert "differential_equations" in loaded
    assert "field_dynamics" in loaded
    assert "field_dynamics.bundles3d" in loaded
