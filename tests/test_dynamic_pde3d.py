import pytest

from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations import (
    ComplexPDEProblem3D,
    ComplexPDESliceView3D,
    SecondOrderScalarPDEProblem3D,
    UniformGrid1D,
    UniformGrid3D,
    integrate_scalar_grid_3d,
    upwind_advection_3d,
)


def _grid(count: int = 3) -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, count)
    return UniformGrid3D(axis, axis, axis)


def test_integrate_scalar_grid_3d_unit_cube_constant() -> None:
    grid = _grid()
    assert integrate_scalar_grid_3d((1.0,) * grid.count, grid) == pytest.approx(1.0)


def test_upwind_advection_3d_linear_x_field() -> None:
    grid = _grid()
    values = tuple(x for x, _y, _z in grid.coordinates)
    velocity = TimeDependentVectorField3D(
        evaluator=lambda _position, _time: Vec3(1.0, 0.0, 0.0),
        name="uniform_x",
    )

    advection = upwind_advection_3d(
        values,
        grid,
        velocity,
        time=0.0,
        boundary="fixed",
    )

    center = grid.flat_index(1, 1, 1)
    assert advection[center] == pytest.approx(1.0)


def test_second_order_3d_lowers_to_ode() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["partial_differential_equations.second_order3d"],
    )
    problem_type = registry.require("pde.second_order_problem3d")
    solve = registry.require("pde.solve_second_order_3d")
    grid = _grid()

    solution = solve(
        problem_type(
            grid=grid,
            initial_values=(0.0,) * grid.count,
            initial_velocity=(1.0,) * grid.count,
            acceleration_rhs=lambda _time, _grid, values, _velocities: (0.0,) * len(values),
            name="free_second_order",
        ),
        end_time=1.0,
        steps=4,
    )

    assert solution.values[-1] == pytest.approx((1.0,) * grid.count)
    assert solution.velocities[-1] == pytest.approx((1.0,) * grid.count)


def test_complex_3d_solution_explicit_slice_compiles_to_scene() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["partial_differential_equations.complex_views3d"])
    problem_type = registry.require("pde.complex.problem3d")
    solve = registry.require("pde.complex.solve_method_of_lines_3d")
    grid = _grid()

    solution = solve(
        problem_type(
            grid=grid,
            initial_values=(1.0 + 2.0j,) * grid.count,
            rhs=lambda _time, _grid, values: (0.0j,) * len(values),
            name="static_complex3d",
        ),
        end_time=1.0,
        steps=2,
    )
    view = ComplexPDESliceView3D(
        solution=solution,
        axis="z",
        index=1,
        component="magnitude_squared",
    )
    scene = registry.compile_scene(view)

    assert len(scene.primitives) == 1
    assert scene.timeline is not None
    sampled = scene.sample(0.5)
    assert len(sampled.primitives) == 1
