from __future__ import annotations

import math

from spectra.domains.differential_equations.domain import (
    ODE_FIRST_ORDER_SOLVER_ROLE,
    FirstOrderSystem,
    ODESolution,
)
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.numerics import NumericalExecutionDescriptor, NumericalMethodDescriptor


RK45_METHOD = NumericalMethodDescriptor(
    method_id="rk45.dormand-prince",
    family="embedded-runge-kutta",
    implementation="spectra.reference.rk45",
    order=5,
    adaptive=True,
    reference_implementation=True,
    notes=("Dormand-Prince 5(4) adaptive reference solver",),
)

RK45_EXECUTION = NumericalExecutionDescriptor(
    kind="python",
    backend="spectra.reference",
    precision="float64",
    supports_in_place=False,
    batched=False,
)


def _combine(
    state: tuple[float, ...],
    h: float,
    terms: tuple[tuple[float, tuple[float, ...]], ...],
) -> tuple[float, ...]:
    size = len(state)
    if any(len(derivative) != size for _coefficient, derivative in terms):
        raise ValueError("adaptive ODE derivative dimension mismatch")
    return tuple(
        state[index]
        + h * sum(coefficient * derivative[index] for coefficient, derivative in terms)
        for index in range(size)
    )


def solve_rk45(
    system: FirstOrderSystem,
    *,
    end_time: float,
    steps: int = 64,
    rtol: float = 1e-6,
    atol: float = 1e-9,
    max_steps: int = 100000,
) -> ODESolution:
    """Adaptive Dormand-Prince RK45 with `steps` used as the initial step-size hint."""

    if steps < 1:
        raise ValueError("RK45 steps hint must be >= 1")
    if end_time <= system.initial_time:
        raise ValueError("RK45 end_time must exceed initial_time")
    if not math.isfinite(rtol) or rtol <= 0.0:
        raise ValueError("RK45 rtol must be finite and positive")
    if not math.isfinite(atol) or atol <= 0.0:
        raise ValueError("RK45 atol must be finite and positive")
    if max_steps < 1:
        raise ValueError("RK45 max_steps must be >= 1")

    time = float(system.initial_time)
    state = tuple(float(value) for value in system.initial_state)
    duration = float(end_time) - time
    h = duration / steps
    minimum_h = max(abs(duration), 1.0) * 1e-15
    times = [time]
    states = [state]
    attempts = 0

    while time < end_time:
        attempts += 1
        if attempts > max_steps:
            raise RuntimeError("RK45 exceeded max_steps before reaching end_time")
        h = min(h, end_time - time)
        if h <= minimum_h:
            raise RuntimeError("RK45 step size underflow")

        k1 = tuple(float(value) for value in system.derivative(time, state))
        y2 = _combine(state, h, ((1.0 / 5.0, k1),))
        k2 = tuple(float(value) for value in system.derivative(time + h * (1.0 / 5.0), y2))
        y3 = _combine(state, h, ((3.0 / 40.0, k1), (9.0 / 40.0, k2)))
        k3 = tuple(float(value) for value in system.derivative(time + h * (3.0 / 10.0), y3))
        y4 = _combine(
            state,
            h,
            ((44.0 / 45.0, k1), (-56.0 / 15.0, k2), (32.0 / 9.0, k3)),
        )
        k4 = tuple(float(value) for value in system.derivative(time + h * (4.0 / 5.0), y4))
        y5_stage = _combine(
            state,
            h,
            (
                (19372.0 / 6561.0, k1),
                (-25360.0 / 2187.0, k2),
                (64448.0 / 6561.0, k3),
                (-212.0 / 729.0, k4),
            ),
        )
        k5 = tuple(float(value) for value in system.derivative(time + h * (8.0 / 9.0), y5_stage))
        y6 = _combine(
            state,
            h,
            (
                (9017.0 / 3168.0, k1),
                (-355.0 / 33.0, k2),
                (46732.0 / 5247.0, k3),
                (49.0 / 176.0, k4),
                (-5103.0 / 18656.0, k5),
            ),
        )
        k6 = tuple(float(value) for value in system.derivative(time + h, y6))
        fifth_order = _combine(
            state,
            h,
            (
                (35.0 / 384.0, k1),
                (500.0 / 1113.0, k3),
                (125.0 / 192.0, k4),
                (-2187.0 / 6784.0, k5),
                (11.0 / 84.0, k6),
            ),
        )
        k7 = tuple(float(value) for value in system.derivative(time + h, fifth_order))
        fourth_order = _combine(
            state,
            h,
            (
                (5179.0 / 57600.0, k1),
                (7571.0 / 16695.0, k3),
                (393.0 / 640.0, k4),
                (-92097.0 / 339200.0, k5),
                (187.0 / 2100.0, k6),
                (1.0 / 40.0, k7),
            ),
        )

        if not all(math.isfinite(value) for value in fifth_order + fourth_order):
            raise ValueError("RK45 produced non-finite state")
        scaled_error_squared = 0.0
        for old, new, lower in zip(state, fifth_order, fourth_order, strict=True):
            scale = atol + rtol * max(abs(old), abs(new))
            error = (new - lower) / scale
            scaled_error_squared += error * error
        error_norm = math.sqrt(scaled_error_squared / len(state))

        if error_norm <= 1.0:
            time = min(time + h, float(end_time))
            state = fifth_order
            times.append(time)
            states.append(state)

        if error_norm == 0.0:
            factor = 5.0
        else:
            factor = 0.9 * error_norm ** (-0.2)
            factor = min(5.0, max(0.2, factor))
        h *= factor

    return ODESolution(times=tuple(times), states=tuple(states))


class AdaptiveReferenceSolversDomain:
    """Optional adaptive first-order ODE implementation for the shared solver role."""

    name = "differential_equations.adaptive_reference"
    version = "1"
    dependencies = (
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solver_role.first_order"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("ode.first_order.rk45_reference", solve_rk45)
        registry.provide("ode.first_order.rk45_reference.method", RK45_METHOD)
        registry.provide("ode.first_order.rk45_reference.execution", RK45_EXECUTION)
        registry.register_numerical_solver(
            ODE_FIRST_ORDER_SOLVER_ROLE,
            "rk45.reference",
            solve_rk45,
            RK45_METHOD,
            tags=("reference", "python", "adaptive"),
            execution=RK45_EXECUTION,
        )


__all__ = [
    "AdaptiveReferenceSolversDomain",
    "RK45_EXECUTION",
    "RK45_METHOD",
    "solve_rk45",
]
