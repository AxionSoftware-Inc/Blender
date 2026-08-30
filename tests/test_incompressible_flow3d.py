import pytest

from spectra.core.types import Vec3
from spectra.core.units import (
    KILOGRAM_PER_CUBIC_METER,
    SQUARE_METER_PER_SECOND,
    Quantity,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    UniformGrid1D,
    UniformGrid3D,
    vector_upwind_advection_grid_3d,
)
from spectra.domains.physics import IncompressibleFlowProblem3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_vector_upwind_advection_3d_constant_field_is_zero() -> None:
    grid = _grid()
    state = (Vec3(1.0, -2.0, 0.5),) * grid.count
    result = vector_upwind_advection_grid_3d(state, grid, boundary="fixed")

    assert all(vector == Vec3(0.0, 0.0, 0.0) for vector in result)


def test_incompressible_flow_3d_zero_state_remains_zero() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.incompressible_flow.3d"])
    grid = _grid()
    solve = registry.require("physics.incompressible_flow.simulate3d")

    solution = solve(
        IncompressibleFlowProblem3D(
            grid=grid,
            initial_velocity=(Vec3(0.0, 0.0, 0.0),) * grid.count,
            density=Quantity(1.0, KILOGRAM_PER_CUBIC_METER),
            kinematic_viscosity=Quantity(0.0, SQUARE_METER_PER_SECOND),
            velocity_boundary="fixed",
            pressure_boundary="zero_gradient",
        ),
        end_time=0.1,
        steps=2,
        pressure_max_iterations=20,
        pressure_tolerance=1e-10,
    )

    assert "partial_differential_equations.operators3d" in loaded
    assert "partial_differential_equations.elliptic3d" in loaded
    assert len(solution.states) == 3
    assert all(
        vector == Vec3(0.0, 0.0, 0.0)
        for state in solution.states
        for vector in state.velocity
    )
    assert all(state.max_divergence == pytest.approx(0.0) for state in solution.states)
    assert all(state.pressure_converged for state in solution.states)


def test_incompressible_flow_3d_history_returns_to_generic_fields_and_scene() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["physics.incompressible_flow.views3d"])
    grid = _grid()
    solve = registry.require("physics.incompressible_flow.simulate3d")
    solution = solve(
        IncompressibleFlowProblem3D(
            grid=grid,
            initial_velocity=(Vec3(0.0, 0.0, 0.0),) * grid.count,
            density=Quantity(1.0, KILOGRAM_PER_CUBIC_METER),
            kinematic_viscosity=Quantity(0.0, SQUARE_METER_PER_SECOND),
        ),
        end_time=0.1,
        steps=2,
        pressure_max_iterations=20,
        pressure_tolerance=1e-10,
    )

    fields = registry.require("physics.incompressible_flow.fields_from_solution3d")(solution)
    assert fields.velocity.evaluate(Vec3(0.5, 0.5, 0.5), 0.05) == Vec3(0.0, 0.0, 0.0)
    assert fields.pressure.evaluate(Vec3(0.5, 0.5, 0.5), 0.05) == pytest.approx(0.0)

    animation = registry.require("physics.incompressible_flow.velocity_animation3d")(
        solution,
        temporal_samples=2,
    )
    scene = registry.compile_scene(animation)
    assert len(scene.primitives) == 1
    assert scene.timeline is not None

    pathline_problem = registry.require("physics.incompressible_flow.pathline_problem3d")(
        solution,
        Vec3(0.5, 0.5, 0.5),
    )
    pathline = registry.require("field_dynamics.solve_pathline")(
        pathline_problem,
        end_time=0.1,
        steps=2,
    )
    assert pathline.positions[-1] == Vec3(0.5, 0.5, 0.5)
