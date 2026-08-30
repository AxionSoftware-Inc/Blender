from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spectra.domains.registry import DomainRegistry


State = tuple[float, ...]
DerivativeFunction = Callable[[float, State], State]


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
    """Deterministic fixed-step RK4 reference solver.

    This is intentionally a small reference implementation. Faster/adaptive
    solvers can replace it behind the same capability contract later.
    """
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


class DifferentialEquationsDomain:
    name = "differential_equations"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("ode.first_order_system", FirstOrderSystem)
        registry.register_semantic_type("ode.solution", ODESolution)
        registry.provide("ode.first_order_system", FirstOrderSystem)
        registry.provide("ode.solve_rk4", solve_rk4)
