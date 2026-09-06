from __future__ import annotations

import math

import pytest

from spectra.domains.differential_equations.domain import (
    DifferentialEquationsDomain,
    FirstOrderSystem,
    ODE_FIRST_ORDER_SOLVER_ROLE,
    solve_rk4,
)
from spectra.domains.differential_equations.native_cpu import (
    NATIVE_CPU_AVAILABLE,
    NATIVE_RK4_EXECUTION,
    NATIVE_RK4_METHOD,
    NativeCpuOdeDomain,
    solve_native_rk4,
)
from spectra.domains.registry import DomainRegistry
from spectra.numerics import NumericalSolverRequirements


def _decay(_time: float, state: tuple[float, ...]) -> tuple[float, ...]:
    return (-state[0],)


def _system() -> FirstOrderSystem:
    return FirstOrderSystem(
        derivative=_decay,
        initial_time=0.0,
        initial_state=(1.0,),
        name="decay",
    )


def _registry() -> DomainRegistry:
    registry = DomainRegistry()
    registry.add_domain(DifferentialEquationsDomain())
    registry.add_domain(NativeCpuOdeDomain())
    return registry


def test_native_cpu_provider_matches_reference_rk4() -> None:
    system = _system()
    reference = solve_rk4(system, end_time=1.0, steps=128)
    candidate = solve_native_rk4(system, end_time=1.0, steps=128)

    assert candidate.times == reference.times
    assert len(candidate.states) == len(reference.states)
    for left, right in zip(candidate.states, reference.states, strict=True):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert math.isclose(a, b, rel_tol=1e-13, abs_tol=1e-13)


def test_native_cpu_execution_metadata_is_truthful() -> None:
    assert NATIVE_RK4_METHOD.method_id == "rk4.fixed"
    assert NATIVE_RK4_METHOD.order == 4
    assert NATIVE_RK4_METHOD.adaptive is False

    if NATIVE_CPU_AVAILABLE:
        assert NATIVE_RK4_EXECUTION.kind == "cpu"
        assert NATIVE_RK4_EXECUTION.backend == "spectra.native_cpu"
        assert NATIVE_RK4_EXECUTION.device == "host-cpu"
        assert NATIVE_RK4_METHOD.reference_implementation is False
    else:
        assert NATIVE_RK4_EXECUTION.kind == "python"
        assert NATIVE_RK4_EXECUTION.backend == "spectra.native_cpu.python_fallback"
        assert NATIVE_RK4_EXECUTION.device is None
        assert NATIVE_RK4_METHOD.reference_implementation is True


def test_cpu_only_solver_selection_is_truthful() -> None:
    registry = _registry()
    requirements = NumericalSolverRequirements(
        execution_kinds=("cpu",),
        minimum_order=4,
        adaptive=False,
        allow_reference=False,
    )

    if not NATIVE_CPU_AVAILABLE:
        with pytest.raises(LookupError):
            registry.select_numerical_solver_for_problem(
                ODE_FIRST_ORDER_SOLVER_ROLE,
                _system(),
                requirements,
            )
        return

    selected = registry.select_numerical_solver_for_problem(
        ODE_FIRST_ORDER_SOLVER_ROLE,
        _system(),
        requirements,
    )
    assert selected.implementation_id == "rk4.native_cpu"
    assert selected.execution.kind == "cpu"
    assert selected.execution.backend == "spectra.native_cpu"


def test_tracked_cpu_selection_reports_actual_execution() -> None:
    registry = _registry()
    solve_selected_tracked = registry.require("ode.solve_first_order_selected.tracked")
    requirements = NumericalSolverRequirements(
        execution_kinds=(("cpu",) if NATIVE_CPU_AVAILABLE else ("python",)),
        minimum_order=4,
        adaptive=False,
        allow_reference=not NATIVE_CPU_AVAILABLE,
        required_tags=(("native",) if NATIVE_CPU_AVAILABLE else ("fallback",)),
    )
    tracked = solve_selected_tracked(
        _system(),
        requirements=requirements,
        end_time=1.0,
        steps=32,
    )

    assert tracked.run.solver_role == ODE_FIRST_ORDER_SOLVER_ROLE
    assert tracked.run.implementation_id == "rk4.native_cpu"
    assert tracked.run.execution_kind == ("cpu" if NATIVE_CPU_AVAILABLE else "python")
    assert tracked.run.backend == (
        "spectra.native_cpu"
        if NATIVE_CPU_AVAILABLE
        else "spectra.native_cpu.python_fallback"
    )
