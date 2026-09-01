import math

import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem, ODESolution
from spectra.domains.experiments import MetricSpec, ParameterAxis, ParameterSweep
from spectra.domains.partial_differential_equations import (
    ScalarPDEProblem3D,
    UniformGrid1D,
    UniformGrid3D,
)
from spectra.numerics import (
    NumericalExecutionDescriptor,
    NumericalMethodDescriptor,
    NumericalSolverRequirements,
)


EULER_METHOD = NumericalMethodDescriptor(
    method_id="euler.fixed",
    family="explicit-euler",
    implementation="tests.euler",
    order=1,
    reference_implementation=False,
)


def _solve_euler(system: FirstOrderSystem, *, end_time: float, steps: int = 8) -> ODESolution:
    dt = (end_time - system.initial_time) / steps
    time = system.initial_time
    state = tuple(system.initial_state)
    times = [time]
    states = [state]
    for _ in range(steps):
        derivative = system.derivative(time, state)
        state = tuple(
            value + dt * delta
            for value, delta in zip(state, derivative, strict=True)
        )
        time += dt
        times.append(time)
        states.append(state)
    return ODESolution(tuple(times), tuple(states))


def test_domain_registry_supports_multiple_solver_implementations_and_default_selection() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])

    assert registry.numerical_solvers.default_implementation_id("ode.first_order") == "rk4.reference"
    assert registry.numerical_solver_method("ode.first_order").order == 4

    registry.register_numerical_solver(
        "ode.first_order",
        "euler.test",
        _solve_euler,
        EULER_METHOD,
    )
    ids = tuple(
        implementation.implementation_id
        for implementation in registry.numerical_solver_implementations("ode.first_order")
    )
    assert ids == ("euler.test", "rk4.reference")

    registry.set_default_numerical_solver("ode.first_order", "euler.test")
    assert registry.numerical_solver_for("ode.first_order") is _solve_euler
    assert registry.numerical_solver_method("ode.first_order").method_id == "euler.fixed"


def test_execution_requirements_select_matching_solver_implementation() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    registry.register_numerical_solver(
        "ode.first_order",
        "euler.gpu.test",
        _solve_euler,
        EULER_METHOD,
        priority=10,
        tags=("gpu", "batched"),
        execution=NumericalExecutionDescriptor(
            kind="gpu",
            backend="test-gpu",
            precision="float32",
            device="test-device",
            supports_in_place=True,
            batched=True,
        ),
    )

    selected = registry.select_numerical_solver(
        "ode.first_order",
        NumericalSolverRequirements(
            execution_kinds=("gpu",),
            precisions=("float32",),
            allow_reference=False,
            required_tags=("batched",),
        ),
    )
    assert selected.implementation_id == "euler.gpu.test"
    assert selected.execution.kind == "gpu"
    assert selected.execution.batched

    with pytest.raises(LookupError):
        registry.select_numerical_solver(
            "ode.first_order",
            NumericalSolverRequirements(
                execution_kinds=("gpu",),
                minimum_order=4,
            ),
        )


def test_problem_compatibility_filters_execution_matches() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    registry.register_numerical_solver(
        "ode.first_order",
        "small-state.gpu.test",
        _solve_euler,
        EULER_METHOD,
        priority=20,
        tags=("gpu",),
        execution=NumericalExecutionDescriptor(
            kind="gpu",
            backend="small-state-gpu",
            precision="float32",
            device="test-device",
        ),
        supports_problem=lambda problem: (
            isinstance(problem, FirstOrderSystem)
            and len(problem.initial_state) <= 4
        ),
    )
    requirements = NumericalSolverRequirements(
        execution_kinds=("gpu",),
        allow_reference=False,
    )
    small = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0, 2.0),
    )
    large = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,) * 8,
    )

    selected = registry.select_numerical_solver_for_problem(
        "ode.first_order",
        small,
        requirements,
    )
    assert selected.implementation_id == "small-state.gpu.test"

    with pytest.raises(LookupError):
        registry.select_numerical_solver_for_problem(
            "ode.first_order",
            large,
            requirements,
        )


def test_pde_time_integration_follows_runtime_default_ode_solver() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations.3d"])
    reference = registry.require("ode.solve_rk4")
    calls: list[str] = []
    spy_method = NumericalMethodDescriptor(
        method_id="spy.rk4",
        family="test-wrapper",
        implementation="tests.spy",
        order=4,
        reference_implementation=False,
    )

    def spy_solver(system: FirstOrderSystem, *, end_time: float, steps: int = 8) -> ODESolution:
        calls.append(system.name)
        return reference(system, end_time=end_time, steps=steps)

    registry.register_numerical_solver(
        "ode.first_order",
        "spy.test",
        spy_solver,
        spy_method,
    )
    registry.set_default_numerical_solver("ode.first_order", "spy.test")

    axis = UniformGrid1D(0.0, 1.0, 3)
    grid = UniformGrid3D(axis, axis, axis)
    problem = ScalarPDEProblem3D(
        grid=grid,
        initial_values=(1.0,) * grid.count,
        rhs=lambda _time, _grid, values: (0.0,) * len(values),
        name="solver_dispatch_probe",
    )
    solve = registry.require("pde.solve_method_of_lines_3d")
    solution = solve(problem, end_time=0.1, steps=2)

    assert calls == ["solver_dispatch_probe"]
    assert solution.states[-1] == pytest.approx((1.0,) * grid.count)

    tracked = registry.require("pde.solve_method_of_lines_3d.tracked")(
        problem,
        end_time=0.1,
        steps=2,
    )
    assert tracked.run.method.stages[-1].method_id == "spy.rk4"


def test_failed_domain_registration_rolls_back_solver_registry_mutation() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])

    class BrokenSolverDomain:
        name = "tests.broken_solver"
        version = "1"
        dependencies = ()

        def register(self, target: DomainRegistry) -> None:
            target.register_numerical_solver(
                "ode.first_order",
                "broken.test",
                _solve_euler,
                EULER_METHOD,
                make_default=True,
            )
            raise RuntimeError("intentional registration failure")

    with pytest.raises(RuntimeError, match="intentional"):
        registry.add_domain(BrokenSolverDomain())

    ids = tuple(
        implementation.implementation_id
        for implementation in registry.numerical_solver_implementations("ode.first_order")
    )
    assert ids == ("rk4.reference",)
    assert registry.numerical_solvers.default_implementation_id("ode.first_order") == "rk4.reference"


def test_parameter_sweep_is_deterministic_and_collects_metrics() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments"])
    run_sweep = registry.require("experiments.run_sweep")

    sweep = ParameterSweep(
        axes=(
            ParameterAxis("x", (1.0, 2.0)),
            ParameterAxis("scale", (10.0, 20.0)),
        ),
        name="grid",
    )
    result = run_sweep(
        sweep,
        lambda parameters: parameters["x"] * parameters["scale"],
        metrics=(MetricSpec("value", lambda output, _parameters: output),),
    )

    assert sweep.case_count == 4
    assert tuple(case.case.case_id for case in result.cases) == (
        "grid.0000",
        "grid.0001",
        "grid.0002",
        "grid.0003",
    )
    assert tuple(case.output for case in result.cases) == (10.0, 20.0, 20.0, 40.0)
    assert tuple(metric.value for _case, metric in result.metric_series("value")) == (
        10.0,
        20.0,
        20.0,
        40.0,
    )


def test_solver_comparison_runs_same_problem_across_implementations() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations", "experiments"])
    registry.register_numerical_solver(
        "ode.first_order",
        "euler.test",
        _solve_euler,
        EULER_METHOD,
    )
    compare = registry.require("experiments.compare_solvers")
    problem = FirstOrderSystem(
        derivative=lambda _time, state: state,
        initial_time=0.0,
        initial_state=(1.0,),
        name="growth",
    )

    comparison = compare(
        "ode.first_order",
        problem,
        solver_kwargs={"end_time": 1.0, "steps": 8},
        metrics=(
            MetricSpec(
                "absolute_error",
                lambda solution, _parameters: abs(solution.states[-1][0] - math.e),
            ),
        ),
        failure_policy="raise",
    )

    assert comparison.experiment.success_count == 2
    errors = {
        case.case.as_dict()["implementation"]: case.metric("absolute_error").value
        for case in comparison.experiment.cases
    }
    assert errors["rk4.reference"] < errors["euler.test"]
