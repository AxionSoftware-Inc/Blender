import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem
from spectra.domains.partial_differential_equations import (
    ScalarPDEProblem3D,
    UniformGrid1D,
    UniformGrid3D,
)
from spectra.numerics import NumericalPipelineDescriptor, NumericalSolverPolicy, NumericalSolverRequirements


def test_tracked_rk4_preserves_existing_solution_contract_and_records_method() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    system = FirstOrderSystem(
        derivative=lambda _time, state: (state[0],),
        initial_time=0.0,
        initial_state=(1.0,),
        name="exponential",
    )

    tracked = registry.require("ode.solve_rk4.tracked")(
        system,
        end_time=1.0,
        steps=8,
    )
    plain = registry.require("ode.solve_rk4")(
        system,
        end_time=1.0,
        steps=8,
    )

    assert tracked.result == plain
    assert tracked.run.method.method_id == "rk4.fixed"
    assert tracked.run.method.order == 4
    assert tracked.run.steps == 8
    assert tracked.run.requested_steps == 8
    assert tracked.run.state_size == 1
    assert tracked.run.solver_role == "ode.first_order"
    assert tracked.run.implementation_id == "rk4.reference"
    assert tracked.run.execution_kind == "python"
    assert tracked.run.backend == "spectra.reference"
    assert tracked.run.precision == "float64"
    assert tracked.run.fixed_step_size == pytest.approx(0.125)


def test_policy_selected_first_order_tracking_records_adaptive_execution() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["differential_equations"])
    catalog.load_capabilities(registry, ["ode.first_order.rk45_reference"])
    registry.set_numerical_solver_policy(
        "ode.first_order",
        NumericalSolverPolicy(
            rules=(NumericalSolverRequirements(adaptive=True, minimum_order=5),),
            fallback_to_default=False,
            name="adaptive_only",
        ),
    )
    system = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
        name="adaptive_exponential",
    )

    tracked = registry.require("ode.solve_first_order.tracked")(
        system,
        end_time=1.0,
        steps=2,
    )

    assert tracked.run.implementation_id == "rk45.reference"
    assert tracked.run.method.method_id == "rk45.dormand-prince"
    assert tracked.run.adaptive
    assert tracked.run.requested_steps == 2
    assert tracked.run.steps == len(tracked.result.times) - 1
    assert tracked.run.steps >= 1
    assert tracked.run.average_step_size == pytest.approx(1.0 / tracked.run.steps)
    with pytest.raises(ValueError, match="adaptive"):
        _ = tracked.run.fixed_step_size


def test_tracked_3d_method_of_lines_reports_composed_pipeline() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        ["partial_differential_equations.3d"],
    )
    axis = UniformGrid1D(0.0, 1.0, 3)
    grid = UniformGrid3D(axis, axis, axis)
    problem = ScalarPDEProblem3D(
        grid=grid,
        initial_values=(2.0,) * grid.count,
        rhs=lambda _time, _grid, values: (0.0,) * len(values),
        name="stationary_scalar",
    )

    tracked = registry.require("pde.solve_method_of_lines_3d.tracked")(
        problem,
        end_time=0.5,
        steps=4,
    )
    method = registry.require("pde.solve_method_of_lines_3d.method")

    assert "differential_equations" in loaded
    assert isinstance(method, NumericalPipelineDescriptor)
    assert tuple(stage.method_id for stage in method.stages) == (
        "method-of-lines.scalar3d",
        "rk4.fixed",
    )
    assert tracked.result.states[-1] == pytest.approx((2.0,) * grid.count)
    assert tracked.run.method == method
    assert tracked.run.steps == 4
    assert tracked.run.requested_steps == 4
    assert tracked.run.implementation_id == "rk4.reference"
    assert tracked.run.state_size == grid.count
    assert tracked.run.fixed_step_size == pytest.approx(0.125)


def test_tracked_3d_method_of_lines_preserves_adaptive_solver_trace() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["partial_differential_equations.3d"])
    catalog.load_capabilities(registry, ["ode.first_order.rk45_reference"])
    registry.set_numerical_solver_policy(
        "ode.first_order",
        NumericalSolverPolicy(
            rules=(NumericalSolverRequirements(adaptive=True, minimum_order=5),),
            fallback_to_default=False,
            name="adaptive_pde",
        ),
    )
    axis = UniformGrid1D(0.0, 1.0, 3)
    grid = UniformGrid3D(axis, axis, axis)
    problem = ScalarPDEProblem3D(
        grid=grid,
        initial_values=(3.0,) * grid.count,
        rhs=lambda _time, _grid, values: (0.0,) * len(values),
        name="adaptive_stationary_scalar",
    )

    tracked = registry.require("pde.solve_method_of_lines_3d.tracked")(
        problem,
        end_time=0.5,
        steps=2,
    )

    assert isinstance(tracked.run.method, NumericalPipelineDescriptor)
    assert tuple(stage.method_id for stage in tracked.run.method.stages) == (
        "method-of-lines.scalar3d",
        "rk45.dormand-prince",
    )
    assert tracked.run.adaptive
    assert tracked.run.implementation_id == "rk45.reference"
    assert tracked.run.requested_steps == 2
    assert tracked.run.steps == len(tracked.result.times) - 1
    assert tracked.result.states[-1] == pytest.approx((3.0,) * grid.count)
    with pytest.raises(ValueError, match="adaptive"):
        _ = tracked.run.fixed_step_size
