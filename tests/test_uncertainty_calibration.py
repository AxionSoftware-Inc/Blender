import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import (
    CalibrationObservation,
    MetricSpec,
    ParameterAxis,
    ParameterSweep,
    UncertainParameter,
    WeightedSample,
)


def test_weighted_uncertainty_propagation_matches_analytical_mean_and_variance() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.uncertainty"])
    propagate = registry.require("experiments.propagate_uncertainty")

    result = propagate(
        (
            UncertainParameter(
                "x",
                (
                    WeightedSample(1.0, 0.25),
                    WeightedSample(3.0, 0.75),
                ),
            ),
        ),
        lambda parameters: parameters["x"],
        metrics=(MetricSpec("value", lambda output, _parameters: output),),
        name="weighted_x",
    )

    summary = result.summary("value")
    assert len(result.cases) == 2
    assert sum(case.scenario.weight for case in result.cases) == pytest.approx(1.0)
    assert summary.mean_si == pytest.approx(2.5)
    assert summary.variance_si_squared == pytest.approx(0.75)
    assert summary.standard_deviation_si == pytest.approx(0.75 ** 0.5)


def test_uncertainty_cartesian_scenario_weights_are_normalized() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.uncertainty"])
    propagate = registry.require("experiments.propagate_uncertainty")

    result = propagate(
        (
            UncertainParameter("a", (WeightedSample(1, 1.0), WeightedSample(2, 3.0))),
            UncertainParameter("b", (WeightedSample(10, 2.0), WeightedSample(20, 1.0))),
        ),
        lambda parameters: parameters["a"] + parameters["b"],
        metrics=(MetricSpec("sum", lambda output, _parameters: output),),
    )

    assert len(result.cases) == 4
    assert tuple(case.scenario.scenario_id for case in result.cases) == (
        "uncertainty.0000",
        "uncertainty.0001",
        "uncertainty.0002",
        "uncertainty.0003",
    )
    assert sum(case.scenario.weight for case in result.cases) == pytest.approx(1.0)


def test_grid_calibration_recovers_exact_candidate_parameter() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.calibration"])
    calibrate = registry.require("experiments.calibrate_grid")

    sweep = ParameterSweep(
        axes=(ParameterAxis("gain", (1.0, 2.0, 3.0)),),
        name="gain_fit",
    )
    result = calibrate(
        sweep,
        lambda parameters: 2.0 * parameters["gain"],
        observations=(
            CalibrationObservation(
                "response",
                observed=4.0,
                extractor=lambda output, _parameters: output,
                scale=1.0,
            ),
        ),
    )

    assert result.parameters == {"gain": 2.0}
    assert result.objective_value == pytest.approx(0.0)
    assert result.residuals[0].normalized_residual == pytest.approx(0.0)


def test_grid_calibration_records_failed_candidates_and_selects_successful_best() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.calibration"])
    calibrate = registry.require("experiments.calibrate_grid")

    sweep = ParameterSweep(
        axes=(ParameterAxis("x", (-1.0, 1.0, 2.0)),),
        name="partial_failure",
    )

    def evaluator(parameters):
        if parameters["x"] < 0.0:
            raise ValueError("invalid physical candidate")
        return parameters["x"]

    result = calibrate(
        sweep,
        evaluator,
        observations=(
            CalibrationObservation(
                "target",
                observed=2.0,
                extractor=lambda output, _parameters: output,
            ),
        ),
        failure_policy="record",
    )

    assert result.experiment.failure_count == 1
    assert result.parameters == {"x": 2.0}
