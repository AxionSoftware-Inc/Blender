import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem, ODESolution
from spectra.numerics import (
    NumericalExecutionDescriptor,
    NumericalMethodDescriptor,
    NumericalSolverPolicy,
    NumericalSolverRequirements,
)


POLICY_METHOD = NumericalMethodDescriptor(
    method_id="policy.euler",
    family="explicit-euler",
    implementation="tests.policy",
    order=1,
    reference_implementation=False,
)


def _euler(system: FirstOrderSystem, *, end_time: float, steps: int = 4) -> ODESolution:
    dt = (end_time - system.initial_time) / steps
    time = system.initial_time
    state = tuple(system.initial_state)
    times = [time]
    states = [state]
    for _ in range(steps):
        derivative = system.derivative(time, state)
        state = tuple(value + dt * delta for value, delta in zip(state, derivative, strict=True))
        time += dt
        times.append(time)
        states.append(state)
    return ODESolution(tuple(times), tuple(states))


def test_policy_prefers_matching_gpu_rule_then_falls_back_to_default() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    registry.register_numerical_solver(
        "ode.first_order",
        "gpu.small",
        _euler,
        POLICY_METHOD,
        priority=100,
        execution=NumericalExecutionDescriptor(
            kind="gpu",
            backend="test-gpu",
            precision="float32",
            device="fake",
        ),
        supports_problem=lambda problem: len(problem.initial_state) <= 2,
    )
    registry.set_numerical_solver_policy(
        "ode.first_order",
        NumericalSolverPolicy(
            rules=(
                NumericalSolverRequirements(
                    execution_kinds=("gpu",),
                    allow_reference=False,
                ),
            ),
            fallback_to_default=True,
            name="gpu_then_default",
        ),
    )

    small = FirstOrderSystem(lambda _time, state: state, 0.0, (1.0, 2.0), name="small")
    large = FirstOrderSystem(lambda _time, state: state, 0.0, (1.0,) * 4, name="large")

    assert registry.numerical_solver_implementation_for_problem(
        "ode.first_order", small
    ).implementation_id == "gpu.small"
    assert registry.numerical_solver_implementation_for_problem(
        "ode.first_order", large
    ).implementation_id == "rk4.reference"


def test_high_level_first_order_dispatch_obeys_active_policy() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    calls: list[str] = []

    def tagged_solver(system: FirstOrderSystem, *, end_time: float, steps: int = 4) -> ODESolution:
        calls.append(system.name)
        return _euler(system, end_time=end_time, steps=steps)

    registry.register_numerical_solver(
        "ode.first_order",
        "tagged.policy",
        tagged_solver,
        POLICY_METHOD,
        tags=("preferred",),
    )
    registry.set_numerical_solver_policy(
        "ode.first_order",
        NumericalSolverPolicy(
            rules=(NumericalSolverRequirements(required_tags=("preferred",)),),
            fallback_to_default=False,
        ),
    )
    problem = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
        name="policy_probe",
    )

    registry.require("ode.solve_first_order")(problem, end_time=0.1, steps=2)
    assert calls == ["policy_probe"]


def test_one_off_requirements_do_not_mutate_global_policy_or_default() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["differential_equations"])
    catalog.load_capabilities(registry, ["ode.first_order.rk45_reference"])
    problem = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
    )

    solution = registry.require("ode.solve_first_order_selected")(
        problem,
        requirements=NumericalSolverRequirements(adaptive=True, minimum_order=5),
        end_time=0.1,
        steps=2,
    )

    assert solution.times[-1] == pytest.approx(0.1)
    assert registry.numerical_solvers.default_implementation_id("ode.first_order") == "rk4.reference"
    assert registry.numerical_solver_policy("ode.first_order") is None


def test_failed_domain_registration_rolls_back_policy_mutation() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])

    class BrokenPolicyDomain:
        name = "tests.broken_policy"
        version = "1"
        dependencies = ()

        def register(self, target: DomainRegistry) -> None:
            target.set_numerical_solver_policy(
                "ode.first_order",
                NumericalSolverPolicy(
                    rules=(NumericalSolverRequirements(minimum_order=4),),
                    name="temporary",
                ),
            )
            raise RuntimeError("intentional policy failure")

    with pytest.raises(RuntimeError, match="intentional policy failure"):
        registry.add_domain(BrokenPolicyDomain())

    assert registry.numerical_solver_policy("ode.first_order") is None
