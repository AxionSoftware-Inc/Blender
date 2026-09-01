import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import MetricSpec, ParameterAxis, ParameterSweep


def test_batched_sweep_preserves_case_order_and_batch_boundaries() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["experiments.batching"])
    run_batched = registry.require("experiments.run_sweep_batched")
    sweep = ParameterSweep(
        axes=(ParameterAxis("x", (1, 2, 3, 4, 5)),),
        name="batch_probe",
    )
    observed_batch_sizes: list[int] = []

    def evaluate(batch):
        observed_batch_sizes.append(len(batch))
        return tuple(case["x"] ** 2 for case in batch)

    result = run_batched(
        sweep,
        evaluate,
        batch_size=2,
        metrics=(MetricSpec("value", lambda output, _parameters: output),),
        capture_environment_snapshot=True,
    )

    assert "experiments" in loaded
    assert "experiments.batching" in loaded
    assert observed_batch_sizes == [2, 2, 1]
    assert result.batch_count == 3
    assert result.experiment.success_count == 5
    assert tuple(case.output for case in result.experiment.cases) == (1, 4, 9, 16, 25)
    assert tuple(
        metric.value
        for _case, metric in result.experiment.metric_series("value")
    ) == (1.0, 4.0, 9.0, 16.0, 25.0)
    assert result.environment is not None
    assert result.environment_fingerprint == result.environment.fingerprint


def test_batched_sweep_validates_output_count() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.batching"])
    run_batched = registry.require("experiments.run_sweep_batched")
    sweep = ParameterSweep(
        axes=(ParameterAxis("x", (1, 2)),),
        name="bad_batch",
    )

    with pytest.raises(ValueError, match="output count"):
        run_batched(
            sweep,
            lambda _batch: (1,),
            batch_size=2,
        )


def test_batched_sweep_can_record_whole_batch_failure() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.batching"])
    run_batched = registry.require("experiments.run_sweep_batched")
    sweep = ParameterSweep(
        axes=(ParameterAxis("x", (1, 2, 3, 4)),),
        name="record_batch_failure",
    )

    def evaluate(batch):
        if batch[0]["x"] == 3:
            raise RuntimeError("simulated device batch failure")
        return tuple(case["x"] for case in batch)

    result = run_batched(
        sweep,
        evaluate,
        batch_size=2,
        failure_policy="record",
    )

    assert result.experiment.success_count == 2
    assert result.experiment.failure_count == 2
    assert result.experiment.cases[2].error == "RuntimeError: simulated device batch failure"
    assert result.experiment.cases[3].error == "RuntimeError: simulated device batch failure"
