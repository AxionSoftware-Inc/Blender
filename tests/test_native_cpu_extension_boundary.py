from __future__ import annotations

import math

from spectra.domains.differential_equations.domain import FirstOrderSystem, solve_rk4
from spectra.domains.differential_equations.native_cpu import (
    NATIVE_CPU_AVAILABLE,
    NATIVE_RK4_EXECUTION,
    NATIVE_RK4_METHOD,
    solve_native_rk4,
)


def _decay(_time: float, state: tuple[float, ...]) -> tuple[float, ...]:
    return (-state[0],)


def test_native_cpu_provider_matches_reference_rk4() -> None:
    system = FirstOrderSystem(
        derivative=_decay,
        initial_time=0.0,
        initial_state=(1.0,),
        name="decay",
    )
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
