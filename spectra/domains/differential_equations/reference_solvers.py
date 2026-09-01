from __future__ import annotations

from spectra.domains.differential_equations.domain import (
    FirstOrderSystem,
    ODE_FIRST_ORDER_SOLVER_ROLE,
    ODESolution,
)
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.numerics import NumericalExecutionDescriptor, NumericalMethodDescriptor


HEUN_METHOD = NumericalMethodDescriptor(
    method_id="heun.fixed",
    family="explicit-runge-kutta",
    implementation="spectra.reference.heun",
    order=2,
    adaptive=False,
    reference_implementation=True,
    notes=("explicit trapezoidal / improved Euler fixed-step reference solver",),
)

HEUN_EXECUTION = NumericalExecutionDescriptor(
    kind="python",
    backend="spectra.reference",
    precision="float64",
    supports_in_place=False,
    batched=False,
)


def solve_heun(
    system: FirstOrderSystem,
    *,
    end_time: float,
    steps: int = 256,
) -> ODESolution:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if end_time <= system.initial_time:
        raise ValueError("end_time must be greater than initial_time")

    dt = (end_time - system.initial_time) / steps
    time = system.initial_time
    state = tuple(float(value) for value in system.initial_state)
    times = [time]
    states = [state]

    for _ in range(steps):
        k1 = tuple(system.derivative(time, state))
        if len(k1) != len(state):
            raise ValueError("ODE derivative dimension mismatch")
        predictor = tuple(
            value + dt * delta
            for value, delta in zip(state, k1, strict=True)
        )
        k2 = tuple(system.derivative(time + dt, predictor))
        if len(k2) != len(state):
            raise ValueError("ODE derivative dimension mismatch")
        state = tuple(
            value + 0.5 * dt * (first + second)
            for value, first, second in zip(state, k1, k2, strict=True)
        )
        time += dt
        times.append(time)
        states.append(state)

    return ODESolution(tuple(times), tuple(states))


class ReferenceODESolversDomain:
    """Optional extra reference implementations for solver comparison/validation."""

    name = "differential_equations.reference_solvers"
    version = "1"
    dependencies = (
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solver_role.first_order"),
    )

    def register(self, registry: DomainRegistry) -> None:
        role = registry.require("ode.solver_role.first_order")
        registry.provide("ode.solve_heun", solve_heun)
        registry.provide("ode.solve_heun.method", HEUN_METHOD)
        registry.provide("ode.solve_heun.execution", HEUN_EXECUTION)
        registry.provide("ode.first_order.heun_reference", "heun.reference")
        registry.register_numerical_solver(
            role,
            "heun.reference",
            solve_heun,
            HEUN_METHOD,
            tags=("reference", "cpu", "fixed-step"),
            execution=HEUN_EXECUTION,
        )
