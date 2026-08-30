import pytest

from spectra.core.primitives import Polyline, Surface, VectorGlyphSet
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import AxisSample, RegularGrid3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D


def test_electrostatic_solution_flows_through_common_potential_views_and_field_lines() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(
        registry,
        ["physics.electrostatic_potential.3d", "physics.potential_fields.views3d"],
    )

    axis = UniformGrid1D(-1.0, 1.0, 5)
    grid = UniformGrid3D(axis, axis, axis)
    potential = tuple(x for x, _y, _z in grid.coordinates)

    problem_type = registry.require("physics.electrostatic_potential.problem3d")
    solve = registry.require("physics.electrostatic_potential.solve3d")
    as_potential = registry.require("physics.electrostatic_potential.potential_field3d")
    solution = solve(
        problem_type(
            grid=grid,
            charge_density=tuple(0.0 for _ in range(grid.count)),
            potential_initial_values=potential,
        ),
        max_iterations=10,
        tolerance=1e-10,
    )
    model = as_potential(solution)

    scalar_slice = registry.require("physics.potential_fields.scalar_slice3d")(
        model,
        axis="z",
        coordinate=0.0,
        u=AxisSample(-1.0, 1.0, 5),
        v=AxisSample(-1.0, 1.0, 5),
        height_scale=0.25,
    )
    slice_scene = registry.compile_scene(scalar_slice)
    assert isinstance(slice_scene.primitives[0], Surface)

    view_grid = RegularGrid3D(
        AxisSample(-0.5, 0.5, 3),
        AxisSample(-0.5, 0.5, 3),
        AxisSample(-0.5, 0.5, 3),
    )
    vector_view = registry.require("physics.potential_fields.vector_view3d")(
        model,
        view_grid,
        vector_scale=0.25,
    )
    vector_scene = registry.compile_scene(vector_view)
    assert isinstance(vector_scene.primitives[0], VectorGlyphSet)
    assert vector_scene.primitives[0].instance_count == 27

    bundle_problem = registry.require("physics.potential_fields.field_lines3d")(
        model,
        (Vec3(0.0, 0.0, 0.0),),
        parameter_length=0.5,
        steps_per_direction=8,
    )
    bundle = registry.require("field_dynamics.solve_integral_curve_bundle3d")(bundle_problem)
    bundle_scene = registry.compile_scene(bundle)
    curve = next(item for item in bundle_scene.primitives if isinstance(item, Polyline))
    assert curve.points[0].x == pytest.approx(0.5, abs=1e-9)
    assert curve.points[-1].x == pytest.approx(-0.5, abs=1e-9)
