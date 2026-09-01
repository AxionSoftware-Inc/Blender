from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from itertools import product
import math
from typing import Any

from spectra.core.units import Unit
from spectra.domains.experiments.domain import MetricSpec, MetricValue
from spectra.domains.registry import DomainDependency, DomainRegistry


CaseEvaluator = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class WeightedSample:
    value: Any
    weight: float

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.weight)) or self.weight <= 0.0:
            raise ValueError("uncertainty sample weight must be finite and positive")
        object.__setattr__(self, "weight", float(self.weight))


@dataclass(frozen=True, slots=True)
class UncertainParameter:
    name: str
    samples: tuple[WeightedSample, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("uncertain parameter name cannot be empty")
        if not self.samples:
            raise ValueError("uncertain parameter requires at least one sample")

    @property
    def total_weight(self) -> float:
        return sum(sample.weight for sample in self.samples)


@dataclass(frozen=True, slots=True)
class UncertaintyScenario:
    scenario_id: str
    parameters: tuple[tuple[str, Any], ...]
    weight: float

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("uncertainty scenario_id cannot be empty")
        if not math.isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError("uncertainty scenario weight must be finite and positive")

    def as_dict(self) -> dict[str, Any]:
        return dict(self.parameters)


@dataclass(frozen=True, slots=True)
class UncertaintyCaseResult:
    scenario: UncertaintyScenario
    output: Any
    metrics: tuple[MetricValue, ...]

    def metric(self, name: str) -> MetricValue:
        for metric in self.metrics:
            if metric.name == name:
                return metric
        raise KeyError(f"unknown uncertainty metric: {name}")


@dataclass(frozen=True, slots=True)
class UncertaintyMetricSummary:
    name: str
    mean_si: float
    variance_si_squared: float
    standard_deviation_si: float
    unit: Unit | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("uncertainty metric summary name cannot be empty")
        if not math.isfinite(self.mean_si):
            raise ValueError("uncertainty metric mean must be finite")
        if not math.isfinite(self.variance_si_squared) or self.variance_si_squared < 0.0:
            raise ValueError("uncertainty metric variance must be finite and non-negative")
        if not math.isfinite(self.standard_deviation_si) or self.standard_deviation_si < 0.0:
            raise ValueError("uncertainty metric standard deviation must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class UncertaintyPropagationResult:
    cases: tuple[UncertaintyCaseResult, ...]
    summaries: tuple[UncertaintyMetricSummary, ...]
    name: str = "uncertainty"

    def __post_init__(self) -> None:
        if not self.cases:
            raise ValueError("uncertainty propagation result cannot be empty")
        if not self.summaries:
            raise ValueError("uncertainty propagation requires metric summaries")
        if not self.name:
            raise ValueError("uncertainty propagation name cannot be empty")

    def summary(self, metric: str) -> UncertaintyMetricSummary:
        for summary in self.summaries:
            if summary.name == metric:
                return summary
        raise KeyError(f"unknown uncertainty metric summary: {metric}")


def _metric_si(metric: MetricValue) -> float:
    return metric.unit.to_si(metric.value) if metric.unit is not None else metric.value


class UncertaintyExperimentsDomain:
    """Deterministic weighted propagation over discrete uncertain parameter samples."""

    name = "experiments.uncertainty"
    version = "1"
    dependencies = (
        DomainDependency("experiments.metric_spec"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def propagate(
            parameters: tuple[UncertainParameter, ...],
            evaluator: CaseEvaluator,
            *,
            metrics: tuple[MetricSpec, ...],
            fixed_parameters: Mapping[str, Any] | None = None,
            name: str = "uncertainty",
        ) -> UncertaintyPropagationResult:
            if not parameters:
                raise ValueError("uncertainty propagation requires at least one parameter")
            names = tuple(parameter.name for parameter in parameters)
            if len(names) != len(set(names)):
                raise ValueError("uncertain parameter names must be unique")
            if not metrics:
                raise ValueError("uncertainty propagation requires at least one metric")
            metric_names = tuple(metric.name for metric in metrics)
            if len(metric_names) != len(set(metric_names)):
                raise ValueError("uncertainty metric names must be unique")

            fixed = dict(fixed_parameters or {})
            overlap = set(fixed).intersection(names)
            if overlap:
                raise ValueError(
                    "fixed parameters overlap uncertain parameters: "
                    + ", ".join(sorted(overlap))
                )

            sample_products = tuple(product(*(parameter.samples for parameter in parameters)))
            raw_weights = tuple(
                math.prod(sample.weight for sample in samples)
                for samples in sample_products
            )
            total_weight = sum(raw_weights)
            if total_weight <= 0.0 or not math.isfinite(total_weight):
                raise ValueError("uncertainty scenario weights are invalid")

            results: list[UncertaintyCaseResult] = []
            for index, (samples, raw_weight) in enumerate(zip(sample_products, raw_weights, strict=True)):
                mapping = dict(fixed)
                sampled_parameters = tuple(
                    (parameter.name, sample.value)
                    for parameter, sample in zip(parameters, samples, strict=True)
                )
                mapping.update(sampled_parameters)
                output = evaluator(mapping)
                values = tuple(
                    MetricValue(
                        name=metric.name,
                        value=float(metric.evaluator(output, mapping)),
                        unit=metric.unit,
                    )
                    for metric in metrics
                )
                results.append(
                    UncertaintyCaseResult(
                        scenario=UncertaintyScenario(
                            scenario_id=f"{name}.{index:04d}",
                            parameters=sampled_parameters,
                            weight=raw_weight / total_weight,
                        ),
                        output=output,
                        metrics=values,
                    )
                )

            summaries = []
            for metric in metrics:
                pairs = tuple(
                    (case.scenario.weight, _metric_si(case.metric(metric.name)))
                    for case in results
                )
                mean = sum(weight * value for weight, value in pairs)
                variance = sum(weight * (value - mean) ** 2 for weight, value in pairs)
                summaries.append(
                    UncertaintyMetricSummary(
                        name=metric.name,
                        mean_si=mean,
                        variance_si_squared=max(variance, 0.0),
                        standard_deviation_si=math.sqrt(max(variance, 0.0)),
                        unit=metric.unit,
                    )
                )

            return UncertaintyPropagationResult(
                cases=tuple(results),
                summaries=tuple(summaries),
                name=name,
            )

        registry.register_semantic_type("experiments.weighted_sample", WeightedSample)
        registry.register_semantic_type("experiments.uncertain_parameter", UncertainParameter)
        registry.register_semantic_type("experiments.uncertainty_scenario", UncertaintyScenario)
        registry.register_semantic_type("experiments.uncertainty_result", UncertaintyPropagationResult)
        registry.provide("experiments.weighted_sample", WeightedSample)
        registry.provide("experiments.uncertain_parameter", UncertainParameter)
        registry.provide("experiments.propagate_uncertainty", propagate)
