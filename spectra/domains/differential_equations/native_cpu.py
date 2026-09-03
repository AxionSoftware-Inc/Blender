from __future__ import annotations

import importlib

from spectra.domains.differential_equations.domain import (
    FirstOrderSystem,
    ODESolution,
    ODE_FIRST_ORDER_SOLVER_ROLE,
    solve_rk4,
)
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.numerics import NumericalExecutionDescriptor, NumericalMethodDescriptor


try:
    _native_kernel = importlib.import_module("spectra._native_cpu")
except ImportError:
    _native_kernel = None

NATIVE_CPU_AVAILABLE = _native_kernel is not None

NATIVE_RK4_METHOD = NumericalMethodDescriptor(
    method_id="rk4.fixed",
    family="explicit-runge-kutta",
    implementation=(
        "spectra.native_cpu.rk4"
        if NATIVE_CPU_AVAILABLE
        else "spectra.native_cpu.python_fallback"
    ),
    order=4,
    adaptive=False,
    reference_implementation=not NATIVE_CPU_AVAILABLE,
    notes=(
        "native CPython C-extension RK4 loop"
        if NATIVE_CPU_AVAILABLE
        else "native extension unavailable; Python RK4 compatibility fallback",
    ),
)

NATIVE_RK4_EXECUTION = NumericalExecutionDescriptor(
    kind="cpu" if NATIVE_CPU_AVAILABLE else "python",
    backend=(
        "spectra.native_cpu"
        if NATIVE_CPU_AVAILABLE
        else "spectra.native_cpu.python_fallback"
    ),
    precision="float64",
    device="host-cpu" if NATIVE_CPU_AVAILABLE else None,
    supports_in_place=False,
    batched=False,
)


def solve_native_rk4(
    system: FirstOrderSystem,
    *,
    end_time: float,
    steps: int = 256,
) -> ODESolution:
    """Run fixed-step RK4 through the native kernel when it is installed.

    Source-tree/test environments without a compiled extension retain a
    deterministic Python fallback, but execution metadata reports that fallback
    honestly as ``kind='python'`` rather than claiming native CPU execution.
    """
    if _native_kernel is None:
        return solve_rk4(system, end_time=end_time, steps=steps)

    times, states = _native_kernel.solve_rk4(
        system.derivative,
        system.initial_time,
        system.initial_state,
        end_time,
        steps,
    )
    return ODESolution(
        times=tuple(float(value) for value in times),
        states=tuple(
            tuple(float(component) for component in state)
            for state in states
        ),
    )


class NativeCpuOdeDomain:
    name = "differential_equations.native_cpu"
    version = "2"
    dependencies = (DomainDependency("ode.first_order_system"),)

    def register(self, registry: DomainRegistry) -> None:
        tags = (
            ("native", "cpu", "fixed-step")
            if NATIVE_CPU_AVAILABLE
            else ("fallback", "python", "fixed-step", "reference")
        )
        registry.register_numerical_solver(
            ODE_FIRST_ORDER_SOLVER_ROLE,
            "rk4.native_cpu",
            solve_native_rk4,
            NATIVE_RK4_METHOD,
            priority=-10,
            tags=tags,
            execution=NATIVE_RK4_EXECUTION,
        )
        registry.provide("ode.first_order.rk4_native_cpu", solve_native_rk4)
        registry.provide("ode.first_order.rk4_native_cpu.available", NATIVE_CPU_AVAILABLE)


__all__ = [
    "NATIVE_CPU_AVAILABLE",
    "NATIVE_RK4_METHOD",
    "NATIVE_RK4_EXECUTION",
    "solve_native_rk4",
    "NativeCpuOdeDomain",
]
