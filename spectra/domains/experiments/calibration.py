from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import math
from typing import Any

from spectra.core.units import Unit
from spectra.domains.experiments.domain import (
    ExperimentCaseResult,
    ExperimentResult,
    MetricSpec,
    ParameterSweep,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


PredictionExtractor = Callable[[Any, Mapping[str, Any]], float]


@dataclass(frozen=True, slots=True)
class CalibrationObservation:
    name: str
    observed: float
    extractor: PredictionExtractor
    unit: Unit | None = None
    scale: float | None = None
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("calibration observation name cannot be empty")
        if not math.isfinite(float(self.observed)):
            raise ValueError("calibration observed value must be finite")
        if not callable(self.extractor):
            raise TypeError("calibration observation extractor must be callable")
        if self.scale is not None and (not math.isfinite(float(self.scale)) or self.scale <= 0.0):
            raise ValueError("calibration observation scale must be finite and positive")
        if not math.isfinite(float(self.weight)) or self.weight <= 0.0:
            raise ValueError("calibration observation weight must be finite and positive")

    @property
    def observed_si(self) -> float:
        return self.unit.to_si(self.observed) if self.unit is not None else float(self.observed)

    @property
    def scale_si(self) -> float:
        if self.scale is not None:
            if self.unit is None:
                return float(self.scale)
            baseline = self.unit.to_si(self.observed)
            return abs(self.unit.to_si(self.observed + self.scale) - baseline)
        return max(abs(self.observed_si), 1.0)

    def prediction_si(self, output: Any, parameters: Mapping[str, Any]) -> float:
        prediction = float(self.extractor(output, parameters))
        if not math.isfinite(prediction):
            raise ValueError(f"calibration prediction is non-finite: {self.name}")
        return self.unit.to_si(prediction) if self.unit is not None else prediction


@dataclass(frozen=True, slots=True)
class CalibrationResidual:
    observation: str
    predicted_si: float
    observed_si: float
    normalized_residual: float

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value)
            for value in (self.predicted_si, self.observed_si, self.normalized_residual)
        ):
            raise ValueError("calibration residual values must be finite")


@dataclass(frozen=True, slots=True)
class CalibrationResult:
    experiment: ExperimentResult
    best_case: ExperimentCaseResult
    residuals: tuple[CalibrationResidual, ...]
    objective_value: float
    name: str = "calibration"

    def __post_init__(self) -> None:
        if not self.best_case.successful:
            raise ValueError("calibration best case must be successful")
        if not math.isfinite(self.objective_value) or self.objective_value < 0.0:
            raise ValueError("calibration objective must be finite and non-negative")
        if not self.name:
            raise ValueError("calibration result name cannot be empty")

    @property
    def parameters(self) -> dict[str, Any]:
        return self.best_case.case.as_dict()


class CalibrationExperimentsDomain:
    """Deterministic candidate-search calibration with weighted least-squares residuals."""

    name = "experiments.calibration"
    version = "1"
    dependencies = (
        DomainDependency("experiments.parameter_sweep"),
        DomainDependency("experiments.run_sweep"),
    )

    def register(self, registry: DomainRegistry) -> None:
        run_sweep = registry.require("experiments.run_sweep")

        def calibrate_grid(
            sweep: ParameterSweep,
            evaluator: Callable[[Mapping[str, Any]], Any],
            *,
            observations: tuple[CalibrationObservation, ...],
            failure_policy: str = "record",
            name: str = "calibration",
        ) -> CalibrationResult:
            if not observations:
                raise ValueError("calibration requires at least one observation")
            names = tuple(observation.name for observation in observations)
            if len(names) != len(set(names)):
                raise ValueError("calibration observation names must be unique")

            def objective(output: Any, parameters: Mapping[str, Any]) -> float:
                total = 0.0
                for observation in observations:
                    predicted = observation.prediction_si(output, parameters)
                    residual = (predicted - observation.observed_si) / observation.scale_si
                    total += observation.weight * residual * residual
                return total

            experiment = run_sweep(
                sweep,
                evaluator,
                metrics=(MetricSpec("calibration_objective", objective),),
                failure_policy=failure_policy,
                name=name,
            )
            successful = tuple(case for case in experiment.cases if case.successful)
            if not successful:
                raise ValueError("calibration produced no successful candidate cases")
            best = min(
                successful,
                key=lambda case: (case.metric("calibration_objective").value, case.case.case_id),
            )
            parameters = best.case.as_dict()
            residuals = tuple(
                CalibrationResidual(
                    observation=observation.name,
                    predicted_si=observation.prediction_si(best.output, parameters),
                    observed_si=observation.observed_si,
                    normalized_residual=(
                        observation.prediction_si(best.output, parameters) - observation.observed_si
                    )
                    / observation.scale_si,
                )
                for observation in observations
            )
            return CalibrationResult(
                experiment=experiment,
                best_case=best,
                residuals=residuals,
                objective_value=best.metric("calibration_objective").value,
                name=name,
            )

        registry.register_semantic_type("experiments.calibration_observation", CalibrationObservation)
        registry.register_semantic_type("experiments.calibration_residual", CalibrationResidual)
        registry.register_semantic_type("experiments.calibration_result", CalibrationResult)
        registry.provide("experiments.calibration_observation", CalibrationObservation)
        registry.provide("experiments.calibrate_grid", calibrate_grid)
