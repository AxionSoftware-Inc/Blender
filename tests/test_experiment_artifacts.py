import json

import pytest

from spectra.core.units import CENTIMETER, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import (
    MetricSpec,
    ParameterAxis,
    ParameterSweep,
    artifact_from_json,
    artifact_to_json,
)


def test_tracked_experiment_artifact_json_round_trip_preserves_units_and_environment() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.artifacts"])
    run_tracked = registry.require("experiments.run_sweep_tracked")
    make_artifact = registry.require("experiments.artifact_from_tracked")

    sweep = ParameterSweep(
        axes=(
            ParameterAxis(
                "length",
                (
                    Quantity(1.0, CENTIMETER),
                    Quantity(2.0, CENTIMETER),
                ),
            ),
        ),
        name="length_scan",
    )
    tracked = run_tracked(
        sweep,
        lambda parameters: parameters["length"].value * 2.0,
        metrics=(MetricSpec("double_length", lambda output, _parameters: output, unit=CENTIMETER),),
    )
    artifact = make_artifact(tracked, metadata=(("purpose", "roundtrip"),))
    payload = artifact_to_json(artifact)
    restored = artifact_from_json(payload)

    assert restored.environment.fingerprint == artifact.environment.fingerprint
    assert restored.fingerprint == artifact.fingerprint
    assert restored.metadata == (("purpose", "roundtrip"),)
    first_value = restored.axes[0].values[0]
    assert isinstance(first_value, Quantity)
    assert first_value.value == pytest.approx(1.0)
    assert first_value.unit == CENTIMETER
    assert restored.cases[1].metrics[0].value == pytest.approx(4.0)
    assert restored.cases[1].metrics[0].unit == CENTIMETER


def test_experiment_artifact_detects_environment_fingerprint_tampering() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.artifacts"])
    tracked = registry.require("experiments.run_sweep_tracked")(
        ParameterSweep((ParameterAxis("x", (1.0, 2.0)),), name="tamper"),
        lambda parameters: parameters["x"],
        metrics=(MetricSpec("value", lambda output, _parameters: output),),
    )
    artifact = registry.require("experiments.artifact_from_tracked")(tracked)
    decoded = json.loads(artifact_to_json(artifact))
    decoded["environment_fingerprint"] = "0" * 64

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        artifact_from_json(json.dumps(decoded))


def test_experiment_artifact_keeps_recorded_failures_without_runtime_outputs() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.artifacts"])

    def evaluator(parameters):
        if parameters["x"] == 2:
            raise RuntimeError("intentional")
        return parameters["x"]

    tracked = registry.require("experiments.run_sweep_tracked")(
        ParameterSweep((ParameterAxis("x", (1, 2, 3)),), name="failures"),
        evaluator,
        metrics=(MetricSpec("value", lambda output, _parameters: output),),
        failure_policy="record",
    )
    artifact = registry.require("experiments.artifact_from_tracked")(tracked)

    assert len(artifact.cases) == 3
    assert artifact.cases[1].error is not None
    assert artifact.cases[1].metrics == ()
