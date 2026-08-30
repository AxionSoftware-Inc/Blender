import pytest

from spectra.core.primitives import Polyline
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    ScalarPDEProblem1D,
    UniformGrid1D,
    second_derivative_1d,
)


def test_second_derivative_matches_quadratic_on_interior_points() -> None:
    grid = UniformGrid1D(-1.0, 1.0, 5)
    values = tuple(x * x for x in grid.coordinates)
    derivative = second_derivative_1d(values, grid, boundary="fixed")

    assert derivative[0] == 0.0
    assert derivative[-1] == 0.0
    assert derivative[1:-1] == pytest.approx((2.0, 2.0, 2.0))


def test_pde_domain_reuses_ode_solver_for_heat_equation_profile() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations"])

    assert "differential_equations" in registry.domains
    solve = registry.require("pde.solve_method_of_lines")
    laplacian = registry.require("pde.second_derivative_1d")

    grid = UniformGrid1D(0.0, 1.0, 5)
    problem = ScalarPDEProblem1D(
        grid=grid,
        initial_values=(0.0, 0.0, 1.0, 0.0, 0.0),
        rhs=lambda _time, spatial_grid, values: tuple(
            0.1 * value
            for value in laplacian(values, spatial_grid, boundary="fixed")
        ),
        name="heat-pulse",
    )
    solution = solve(problem, end_time=0.1, steps=20)

    assert solution.states[-1][0] == pytest.approx(0.0)
    assert solution.states[-1][-1] == pytest.approx(0.0)
    assert solution.states[-1][2] < solution.states[0][2]
    assert solution.states[-1][1] > solution.states[0][1]

    scene = registry.compile_scene(solution)
    assert len(scene.primitives) == 1
    profile = scene.primitives[0]
    assert isinstance(profile, Polyline)
    assert scene.timeline.duration == pytest.approx(0.1)
    halfway = scene.sample(0.05).get("heat-pulse.profile")
    assert isinstance(halfway, Polyline)
    assert halfway.points[2].y < 1.0
