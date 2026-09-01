from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_equations import FirstOrderSystem
from spectra.domains.experiments import (
    MetricSpec,
    ParameterAxis,
    ParameterSweep,
    artifact_from_json,
    artifact_to_json,
    traced_output,
)


def test_traced_sweep_records_selected_solver_per_case() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["differential_equations", "experiments.tracing"],
    )
    solve_tracked = registry.require("ode.solve_first_order.tracked")
    run_sweep_traced = registry.require("experiments.run_sweep_traced")

    def evaluator(parameters):
        rate = parameters["rate"]
        tracked = solve_tracked(
            FirstOrderSystem(
                derivative=lambda _time, state: (rate * state[0],),
                initial_time=0.0,
                initial_state=(1.0,),
                name=f"growth_{rate}",
            ),
            end_time=0.25,
            steps=4,
        )
        return traced_output(tracked.result, tracked)

    result = run_sweep_traced(
        ParameterSweep((ParameterAxis("rate", (1.0, 2.0)),), name="traced_growth"),
        evaluator,
        metrics=(
            MetricSpec(
                "final",
                lambda solution, _parameters: solution.states[-1][0],
            ),
        ),
    )

    assert result.numerical_run_count == 2
    assert result.trace_for("traced_growth.0000").solver_implementations == ("rk4.reference",)
    assert result.trace_for("traced_growth.0001").runs[0].requested_steps == 4
    assert result.experiment.success_count == 2


def test_traced_experiment_artifact_preserves_numerical_run_summary() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["differential_equations", "experiments.artifacts"],
    )
    solve_tracked = registry.require("ode.solve_first_order.tracked")
    run_sweep_traced = registry.require("experiments.run_sweep_traced")

    def evaluator(parameters):
        tracked = solve_tracked(
            FirstOrderSystem(
                derivative=lambda _time, state: (-state[0],),
                initial_time=0.0,
                initial_state=(parameters["initial"],),
                name="decay",
            ),
            end_time=0.5,
            steps=4,
        )
        return traced_output(tracked.result, tracked)

    traced = run_sweep_traced(
        ParameterSweep((ParameterAxis("initial", (1.0,)),), name="artifact_trace"),
        evaluator,
        metrics=(MetricSpec("final", lambda solution, _parameters: solution.states[-1][0]),),
    )
    artifact = registry.require("experiments.artifact_from_traced")(traced)
    restored = artifact_from_json(artifact_to_json(artifact))

    assert len(restored.cases[0].runs) == 1
    run = restored.cases[0].runs[0]
    assert run.method_id == "rk4.fixed"
    assert not run.adaptive
    assert run.solver_role == "ode.first_order"
    assert run.implementation_id == "rk4.reference"
    assert run.execution_kind == "python"
    assert run.backend == "spectra.reference"
    assert run.precision == "float64"
    assert run.steps == 4
    assert run.requested_steps == 4
    assert restored.fingerprint == artifact.fingerprint


def test_traced_sweep_can_record_multiple_solver_runs_for_one_case() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["differential_equations", "experiments.tracing"],
    )
    solve_tracked = registry.require("ode.solve_first_order.tracked")

    def evaluator(parameters):
        first = solve_tracked(
            FirstOrderSystem(
                derivative=lambda _time, state: (parameters["a"],),
                initial_time=0.0,
                initial_state=(0.0,),
                name="stage_a",
            ),
            end_time=0.1,
            steps=2,
        )
        second = solve_tracked(
            FirstOrderSystem(
                derivative=lambda _time, state: (-state[0],),
                initial_time=0.0,
                initial_state=(first.result.states[-1][0],),
                name="stage_b",
            ),
            end_time=0.1,
            steps=2,
        )
        return traced_output(second.result, first, second)

    result = registry.require("experiments.run_sweep_traced")(
        ParameterSweep((ParameterAxis("a", (1.0,)),), name="two_stage"),
        evaluator,
    )

    trace = result.trace_for("two_stage.0000")
    assert len(trace.runs) == 2
    assert tuple(run.tags[0][1] for run in trace.runs) == ("stage_a", "stage_b")
    assert trace.solver_implementations == ("rk4.reference", "rk4.reference")
