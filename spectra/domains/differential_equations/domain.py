from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spectra.domains.registry import DomainRegistry
from spectra.numerics import (
    NumericalExecutionDescriptor,
    NumericalMethodDescriptor,
    NumericalSolverRequirements,
    TrackedNumericalResult,
    fixed_step_record,
)


State = tuple[float, ...]
DerivativeFunction = Callable[[float, State], State]
ODE_FIRST_ORDER_SOLVER_ROLE = "ode.first_order"


RK4_METHOD = NumericalMethodDescriptor(
    method_id="rk4.fixed",
    family="explicit-runge-kutta",
    implementation="spectra.reference.rk4",
    order=4,
    adaptive=False,
    reference_implementation=True,
    notes=("deterministic fixed-step reference solver",),
)

RK4_EXECUTION = NumericalExecutionDescriptor(
    kind="python",
    backend="spectra.reference",
    precision="float64",
    supports_in_place=False,
    batched=False,
)


@dataclass(frozen=True, slots=True)
class FirstOrderSystem:
    derivative: DerivativeFunction
    initial_time: float
    initial_state: State
    name: str = "ode_system"

    def __post_init__(self) -> None:
        if not self.initial_state:
            raise ValueError("ODE initial_state cannot be empty")


@dataclass(frozen=True, slots=True)
class ODESolution:
    times: tuple[float, ...]
    states: tuple[State, ...]

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("ODE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("ODE solution times/states length mismatch")


def _add_scaled(state: State, derivative: State, scale: float) -> State:
    if len(state) != len(derivative):
        raise ValueError("ODE derivative dimension mismatch")
    return tuple(value + scale * delta for value, delta in zip(state, derivative, strict=True))


def solve_rk4(system: FirstOrderSystem, *, end_time: float, steps: int = 256) -> ODESolution:
    """Deterministic fixed-step RK4 reference solver."""
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
        k1 = system.derivative(time, state)
        k2 = system.derivative(time + dt * 0.5, _add_scaled(state, k1, dt * 0.5))
        k3 = system.derivative(time + dt * 0.5, _add_scaled(state, k2, dt * 0.5))
        k4 = system.derivative(time + dt, _add_scaled(state, k3, dt))

        if not (len(k1) == len(k2) == len(k3) == len(k4) == len(state)):
            raise ValueError("ODE derivative dimension mismatch")

        state = tuple(
            value + dt * (a + 2.0 * b + 2.0 * c + d) / 6.0
            for value, a, b, c, d in zip(state, k1, k2, k3, k4, strict=True)
        )
        time += dt
        times.append(time)
        states.append(state)

    return ODESolution(tuple(times), tuple(states))


def solve_rk4_tracked(
    system: FirstOrderSystem,
    *,
    end_time: float,
    steps: int = 256,
) -> TrackedNumericalResult[ODESolution]:
    solution = solve_rk4(system, end_time=end_time, steps=steps)
    return TrackedNumericalResult(
        result=solution,
        run=fixed_step_record(
            RK4_METHOD,
            start_time=system.initial_time,
            end_time=end_time,
            steps=steps,
            state_size=len(system.initial_state),
            tags=(("system", system.name),),
        ),
    )


class DifferentialEquationsDomain:
    name = "differential_equations"
    version = "6"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        def solve_first_order(
            system: FirstOrderSystem,
            *,
            end_time: float,
            steps: int = 256,
        ) -> ODESolution:
            solver = registry.numerical_solver_for_problem(
                ODE_FIRST_ORDER_SOLVER_ROLE,
                system,
            )
            return solver(system, end_time=end_time, steps=steps)

        def solve_first_order_with(
            system: FirstOrderSystem,
            *,
            implementation_id: str,
            end_time: float,
            steps: int = 256,
        ) -> ODESolution:
            implementation = registry.numerical_solvers.implementation(
                ODE_FIRST_ORDER_SOLVER_ROLE,
                implementation_id,
            )
            if not implementation.accepts_problem(system):
                raise LookupError(
                    "selected first-order solver does not support problem: "
                    f"{implementation_id}"
                )
            return implementation.solver(system, end_time=end_time, steps=steps)

        def solve_first_order_selected(
            system: FirstOrderSystem,
            *,
            requirements: NumericalSolverRequirements,
            end_time: float,
            steps: int = 256,
        ) -> ODESolution:
            implementation = registry.select_numerical_solver_for_problem(
                ODE_FIRST_ORDER_SOLVER_ROLE,
                system,
                requirements,
            )
            return implementation.solver(system, end_time=end_time, steps=steps)

        registry.register_semantic_type("ode.first_order_system", FirstOrderSystem)
        registry.register_semantic_type("ode.solution", ODESolution)
        registry.provide("ode.first_order_system", FirstOrderSystem)
        registry.provide("ode.solution", ODESolution)
        registry.provide("ode.solve_rk4", solve_rk4)
        registry.provide("ode.solve_rk4.method", RK4_METHOD)
        registry.provide("ode.solve_rk4.execution", RK4_EXECUTION)
        registry.provide("ode.solve_rk4.tracked", solve_rk4_tracked)
        registry.provide("ode.solver_role.first_order", ODE_FIRST_ORDER_SOLVER_ROLE)
        registry.provide("ode.solve_first_order", solve_first_order, version=3)
        registry.provide("ode.solve_first_order_with", solve_first_order_with, version=3)
        registry.provide("ode.solve_first_order_selected", solve_first_order_selected)
        registry.register_numerical_solver(
            ODE_FIRST_ORDER_SOLVER_ROLE,
            "rk4.reference",
            solve_rk4,
            RK4_METHOD,
            make_default=True,
            tags=("reference", "cpu", "fixed-step"),
            execution=RK4_EXECUTION,
        )
