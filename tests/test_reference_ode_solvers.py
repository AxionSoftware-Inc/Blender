import math

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem
from spectra.domains.experiments import MetricSpec


def _growth_problem() -> FirstOrderSystem:
    return FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
        name="growth",
    )


def test_heun_provider_loads_by_capability_and_registers_second_solver() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    loaded = catalog.load_capabilities(registry, ("ode.first_order.heun_reference",))

    assert set(loaded) == {
        "differential_equations",
        "differential_equations.reference_solvers",
    }
    ids = tuple(
        implementation.implementation_id
        for implementation in registry.numerical_solver_implementations("ode.first_order")
    )
    assert ids == ("heun.reference", "rk4.reference")
    assert registry.require("ode.first_order.heun_reference") == "heun.reference"


def test_heun_convergence_study_recovers_second_order_trend() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load_capabilities(
        registry,
        (
            "ode.first_order.heun_reference",
            "experiments.run_solver_convergence",
        ),
    )
    run = registry.require("experiments.run_solver_convergence")

    result = run(
        "ode.first_order",
        _growth_problem(),
        implementation_id="heun.reference",
        end_time=1.0,
        step_counts=(8, 16, 32, 64),
        error=lambda solution, _problem: abs(solution.states[-1][0] - math.e),
    )

    assert result.method_order == 2
    assert result.latest_observed_order is not None
    assert result.latest_observed_order > 1.8
    assert result.meets_order(tolerance=0.25) is True


def test_solver_comparison_uses_real_registered_reference_implementations() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load_capabilities(
        registry,
        (
            "ode.first_order.heun_reference",
            "experiments.compare_solvers",
        ),
    )
    compare = registry.require("experiments.compare_solvers")

    result = compare(
        "ode.first_order",
        _growth_problem(),
        implementation_ids=("heun.reference", "rk4.reference"),
        solver_kwargs={"end_time": 1.0, "steps": 8},
        metrics=(
            MetricSpec(
                "absolute_error",
                lambda solution, _parameters: abs(solution.states[-1][0] - math.e),
            ),
        ),
        failure_policy="raise",
    )
    errors = {
        case.case.as_dict()["implementation"]: case.metric("absolute_error").value
        for case in result.experiment.cases
    }

    assert errors["rk4.reference"] < errors["heun.reference"]
