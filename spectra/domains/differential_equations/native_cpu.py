from __future__ import annotations

from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.differential_equations.domain import FirstOrderSystem, ODESolution, ODE_FIRST_ORDER_SOLVER_ROLE, solve_rk4
from spectra.numerics import NumericalExecutionDescriptor, NumericalMethodDescriptor

NATIVE_RK4_METHOD = NumericalMethodDescriptor("rk4.fixed.native_cpu", "runge_kutta", "native_cpu", order=4, adaptive=False, reference_implementation=False)
NATIVE_RK4_EXECUTION = NumericalExecutionDescriptor(kind="cpu", backend="native_cpu", precision="float64", supports_in_place=False, batched=False)

def solve_native_rk4(system: FirstOrderSystem, *, end_time: float, steps: int = 256) -> ODESolution:
    """Fixed float64 CPU provider boundary; semantics match the reference RK4."""
    return solve_rk4(system, end_time=end_time, steps=steps)

class NativeCpuOdeDomain:
    name = "differential_equations.native_cpu"
    version = "1"
    dependencies = (DomainDependency("ode.first_order_system"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.register_numerical_solver(
            ODE_FIRST_ORDER_SOLVER_ROLE, "rk4.native_cpu", solve_native_rk4,
            NATIVE_RK4_METHOD, priority=-10, tags=("native", "cpu", "fixed-step"),
            execution=NATIVE_RK4_EXECUTION,
        )
        registry.provide("ode.first_order.rk4_native_cpu", solve_native_rk4)
