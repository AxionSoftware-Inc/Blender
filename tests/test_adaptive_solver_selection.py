import math

import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem
from spectra.domains.partial_differential_equations import (
    ScalarPDEProblem3D,
    UniformGrid1D,
    UniformGrid3D,
)
from spectra.numerics import NumericalSolverRequirements


def test_rk45_reference_solves_exponential_growth_to_tolerance() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load_capabilities(registry, ["ode.first_order.rk45_reference"])
    solve = registry.require("ode.first_order.rk45_reference")

    solution = solve(
        FirstOrderSystem(
            derivative=lambda _time, state: state,
            initial_time=0.0,
            initial_state=(1.0,),
            name="exp_growth",
        ),
        end_time=1.0,
        steps=4,
        rtol=1e-9,
        atol=1e-12,
    )

    assert solution.times[0] == pytest.approx(0.0)
    assert solution.times[-1] == pytest.approx(1.0)
    assert solution.states[-1][0] == pytest.approx(math.e, rel=2e-9, abs=2e-9)
    assert all(right > left for left, right in zip(solution.times, solution.times[1:]))


def test_solver_requirements_can_select_adaptive_rk45() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load_capabilities(registry, ["ode.first_order.rk45_reference"])

    selected = registry.select_numerical_solver(
        "ode.first_order",
        NumericalSolverRequirements(
            execution_kinds=("python",),
            minimum_order=5,
            adaptive=True,
        ),
    )

    assert selected.implementation_id == "rk45.reference"
    assert selected.method.adaptive
    assert selected.effective_order == 5


def test_scalar_pde_3d_accepts_adaptive_default_ode_solver() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["partial_differential_equations.3d"])
    catalog.load_capabilities(registry, ["ode.first_order.rk45_reference"])
    registry.set_default_numerical_solver("ode.first_order", "rk45.reference")

    axis = UniformGrid1D(0.0, 1.0, 3)
    grid = UniformGrid3D(axis, axis, axis)
    problem = ScalarPDEProblem3D(
        grid=grid,
        initial_values=(2.0,) * grid.count,
        rhs=lambda _time, _grid, values: (0.0,) * len(values),
        name="adaptive_zero_rhs",
    )
    solution = registry.require("pde.solve_method_of_lines_3d")(
        problem,
        end_time=0.2,
        steps=4,
    )

    assert solution.times[-1] == pytest.approx(0.2)
    assert solution.states[-1] == pytest.approx((2.0,) * grid.count)
    assert len(solution.times) >= 2
