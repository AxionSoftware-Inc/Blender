from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import math
from typing import Any

from spectra.core.units import Quantity, Unit
from spectra.domains.experiments.domain import MetricSpec
from spectra.domains.registry import DomainDependency, DomainRegistry


CaseEvaluator = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class SensitivityParameter:
    name: str
    baseline: float
    step: float
    unit: Unit | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("sensitivity parameter name cannot be empty")
        if not math.isfinite(float(self.baseline)):
            raise ValueError("sensitivity parameter baseline must be finite")
        if not math.isfinite(float(self.step)) or self.step <= 0.0:
            raise ValueError("sensitivity parameter step must be finite and positive")

    def value(self, numeric: float) -> float | Quantity:
        value = float(numeric)
        return Quantity(value, self.unit) if self.unit is not None else value

    @property
    def baseline_si(self) -> float:
        return self.unit.to_si(self.baseline) if self.unit is not None else float(self.baseline)

    @property
    def step_si(self) -> float:
        return abs(self.unit.to_si(self.baseline + self.step) - self.baseline_si) if self.unit is not None else float(self.step)


@dataclass(frozen=True, slots=True)
class SensitivityEstimate:
    parameter: str
    metric: str
    baseline_parameter_si: float
    baseline_response_si: float
    derivative_si: float
    normalized_sensitivity: float | None

    def __post_init__(self) -> None:
        values = (
            self.baseline_parameter_si,
            self.baseline_response_si,
            self.derivative_si,
        )
        if any(not math.isfinite(value) for value in values):
            raise ValueError("sensitivity estimate values must be finite")
        if self.normalized_sensitivity is not None and not math.isfinite(self.normalized_sensitivity):
            raise ValueError("normalized sensitivity must be finite when present")


@dataclass(frozen=True, slots=True)
class LocalSensitivityResult:
    estimates: tuple[SensitivityEstimate, ...]
    baseline_metrics_si: tuple[tuple[str, float], ...]
    name: str = "local_sensitivity"

    def __post_init__(self) -> None:
        if not self.estimates:
            raise ValueError("local sensitivity result cannot be empty")
        if not self.name:
            raise ValueError("local sensitivity result name cannot be empty")

    def estimate(self, parameter: str, metric: str) -> SensitivityEstimate:
        for estimate in self.estimates:
            if estimate.parameter == parameter and estimate.metric == metric:
                return estimate
        raise KeyError(f"unknown sensitivity estimate: {parameter}/{metric}")


def _metric_si(metric: MetricSpec, output: Any, parameters: Mapping[str, Any]) -> float:
    value = float(metric.evaluator(output, parameters))
    if not math.isfinite(value):
        raise ValueError(f"sensitivity metric returned non-finite value: {metric.name}")
    return metric.unit.to_si(value) if metric.unit is not None else value


class SensitivityExperimentsDomain:
    """Unit-aware local central-difference sensitivity for arbitrary experiment evaluators."""

    name = "experiments.sensitivity"
    version = "1"
    dependencies = (
        DomainDependency("experiments.metric_spec"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def local_sensitivity(
            parameters: tuple[SensitivityParameter, ...],
            evaluator: CaseEvaluator,
            *,
            metrics: tuple[MetricSpec, ...],
            fixed_parameters: Mapping[str, Any] | None = None,
            name: str = "local_sensitivity",
        ) -> LocalSensitivityResult:
            if not parameters:
                raise ValueError("local sensitivity requires at least one parameter")
            names = tuple(parameter.name for parameter in parameters)
            if len(names) != len(set(names)):
                raise ValueError("sensitivity parameter names must be unique")
            if not metrics:
                raise ValueError("local sensitivity requires at least one metric")
            metric_names = tuple(metric.name for metric in metrics)
            if len(metric_names) != len(set(metric_names)):
                raise ValueError("sensitivity metric names must be unique")

            base_mapping = dict(fixed_parameters or {})
            overlap = set(base_mapping).intersection(names)
            if overlap:
                raise ValueError(
                    "fixed parameters overlap sensitivity parameters: "
                    + ", ".join(sorted(overlap))
                )
            for parameter in parameters:
                base_mapping[parameter.name] = parameter.value(parameter.baseline)

            baseline_output = evaluator(base_mapping)
            baseline_metrics = tuple(
                (metric.name, _metric_si(metric, baseline_output, base_mapping))
                for metric in metrics
            )
            baseline_by_name = dict(baseline_metrics)

            estimates: list[SensitivityEstimate] = []
            for parameter in parameters:
                lower_mapping = dict(base_mapping)
                upper_mapping = dict(base_mapping)
                lower_mapping[parameter.name] = parameter.value(parameter.baseline - parameter.step)
                upper_mapping[parameter.name] = parameter.value(parameter.baseline + parameter.step)
                lower_output = evaluator(lower_mapping)
                upper_output = evaluator(upper_mapping)
                denominator = 2.0 * parameter.step_si
                if denominator <= 0.0 or not math.isfinite(denominator):
                    raise ValueError("sensitivity parameter has invalid SI perturbation")

                for metric in metrics:
                    lower = _metric_si(metric, lower_output, lower_mapping)
                    upper = _metric_si(metric, upper_output, upper_mapping)
                    derivative = (upper - lower) / denominator
                    baseline_response = baseline_by_name[metric.name]
                    normalized = None
                    if baseline_response != 0.0:
                        normalized = derivative * parameter.baseline_si / baseline_response
                    estimates.append(
                        SensitivityEstimate(
                            parameter=parameter.name,
                            metric=metric.name,
                            baseline_parameter_si=parameter.baseline_si,
                            baseline_response_si=baseline_response,
                            derivative_si=derivative,
                            normalized_sensitivity=normalized,
                        )
                    )

            return LocalSensitivityResult(
                estimates=tuple(estimates),
                baseline_metrics_si=baseline_metrics,
                name=name,
            )

        registry.register_semantic_type("experiments.sensitivity_parameter", SensitivityParameter)
        registry.register_semantic_type("experiments.sensitivity_estimate", SensitivityEstimate)
        registry.register_semantic_type("experiments.local_sensitivity_result", LocalSensitivityResult)
        registry.provide("experiments.sensitivity_parameter", SensitivityParameter)
        registry.provide("experiments.local_sensitivity", local_sensitivity)
