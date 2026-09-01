import math

import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem


def test_rk4_convergence_study_recovers_fourth_order_trend() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["experiments.convergence"])
    run = registry.require("experiments.run_solver_convergence")
    problem = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
        name="exp_growth",
    )

    result = run(
        "ode.first_order",
        problem,
        end_time=1.0,
        step_counts=(4, 8, 16, 32),
        error=lambda solution, _problem: abs(solution.states[-1][0] - math.e),
    )

    assert "differential_equations" in loaded
    assert "experiments.convergence" in loaded
    assert result.implementation_id == "rk4.reference"
    assert result.method_order == 4
    assert result.finest.error < result.samples[0].error
    assert result.latest_observed_order is not None
    assert result.latest_observed_order > 3.5
    assert result.meets_order(tolerance=0.5) is True


def test_convergence_study_rejects_non_increasing_refinement() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.convergence"])
    run = registry.require("experiments.run_solver_convergence")
    problem = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        run(
            "ode.first_order",
            problem,
            end_time=1.0,
            step_counts=(8, 8, 16),
            error=lambda solution, _problem: abs(solution.states[-1][0] - math.e),
        )
