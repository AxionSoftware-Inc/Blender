import pytest

from spectra.core.primitives import Surface
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    ScalarPDEProblem3D,
    ScalarPDESliceView3D,
    ScalarPDESolution3D,
    UniformGrid1D,
    UniformGrid3D,
    laplacian_3d,
    scalar_field_from_grid_3d,
)


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(-1.0, 1.0, 5)
    return UniformGrid3D(axis, axis, axis)


def test_quadratic_3d_laplacian_is_six_interior() -> None:
    grid = _grid()
    values = tuple(x * x + y * y + z * z for x, y, z in grid.coordinates)
    result = laplacian_3d(values, grid, boundary="fixed")
    center = grid.flat_index(2, 2, 2)
    assert result[center] == pytest.approx(6.0)


def test_trilinear_adapter_is_exact_for_linear_field() -> None:
    grid = _grid()
    values = tuple(x + 2.0 * y - 3.0 * z for x, y, z in grid.coordinates)
    field = scalar_field_from_grid_3d(grid, values)
    point = Vec3(0.25, -0.35, 0.4)
    assert field.evaluate(point) == pytest.approx(
        point.x + 2.0 * point.y - 3.0 * point.z
    )


def test_3d_slice_view_reuses_existing_surface_pipeline() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations.slices3d"])
    grid = _grid()
    state0 = tuple(x + y + z for x, y, z in grid.coordinates)
    state1 = tuple(value + 1.0 for value in state0)
    solution = ScalarPDESolution3D(
        grid=grid,
        times=(0.0, 1.0),
        states=(state0, state1),
        name="field3d",
    )
    view = ScalarPDESliceView3D(solution=solution, axis="z", index=2)
    scene = registry.compile_scene(view)
    assert isinstance(scene.primitives[0], Surface)
    assert len(scene.primitives[0].vertices) == grid.x.count * grid.y.count
    assert scene.timeline.duration == pytest.approx(1.0)


def test_3d_method_of_lines_zero_rhs_stays_constant() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations.3d"])
    grid = _grid()
    initial = tuple(2.5 for _ in range(grid.count))
    problem = ScalarPDEProblem3D(
        grid=grid,
        initial_values=initial,
        rhs=lambda _time, _grid, values: tuple(0.0 for _ in values),
    )
    solution = registry.require("pde.solve_method_of_lines_3d")(
        problem,
        end_time=0.1,
        steps=4,
    )
    assert solution.states[-1] == pytest.approx(initial)
