from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from spectra.domains.experiments.domain import (
    ExperimentCaseResult,
    ExperimentResult,
    MetricSpec,
    MetricValue,
    ParameterSweep,
)
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.reproducibility import ScientificEnvironmentSnapshot, capture_environment


BatchFailurePolicy = Literal["raise", "record"]
BatchCaseEvaluator = Callable[[tuple[Mapping[str, Any], ...]], tuple[Any, ...]]


@dataclass(frozen=True, slots=True)
class BatchedExperimentResult:
    experiment: ExperimentResult
    batch_size: int
    batch_count: int
    environment: ScientificEnvironmentSnapshot | None = None

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError("experiment batch_size must be >= 1")
        if self.batch_count < 1:
            raise ValueError("experiment batch_count must be >= 1")
        expected_batches = (len(self.experiment.cases) + self.batch_size - 1) // self.batch_size
        if self.batch_count != expected_batches:
            raise ValueError("experiment batch_count does not match case count/batch size")

    @property
    def environment_fingerprint(self) -> str | None:
        if self.environment is None:
            return None
        return self.environment.fingerprint


class BatchedExperimentsDomain:
    """Deterministic batch execution for native/GPU/vectorized experiment evaluators."""

    name = "experiments.batching"
    version = "1"
    dependencies = (
        DomainDependency("experiments.parameter_sweep"),
        DomainDependency("experiments.metric_spec"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def run_batched(
            sweep: ParameterSweep,
            evaluator: BatchCaseEvaluator,
            *,
            batch_size: int,
            metrics: tuple[MetricSpec, ...] = (),
            failure_policy: BatchFailurePolicy = "raise",
            capture_environment_snapshot: bool = False,
            name: str | None = None,
        ) -> BatchedExperimentResult:
            if batch_size < 1:
                raise ValueError("experiment batch_size must be >= 1")
            if failure_policy not in {"raise", "record"}:
                raise ValueError("experiment failure_policy must be 'raise' or 'record'")
            metric_names = tuple(metric.name for metric in metrics)
            if len(metric_names) != len(set(metric_names)):
                raise ValueError("experiment metric names must be unique")

            cases = sweep.cases()
            results: list[ExperimentCaseResult] = []
            batch_count = 0
            for start in range(0, len(cases), batch_size):
                batch_count += 1
                batch = cases[start : start + batch_size]
                parameters = tuple(case.as_dict() for case in batch)
                try:
                    outputs = tuple(evaluator(parameters))
                    if len(outputs) != len(batch):
                        raise ValueError(
                            "batched experiment evaluator output count must match input case count"
                        )
                    for case, params, output in zip(batch, parameters, outputs, strict=True):
                        metric_values = tuple(
                            MetricValue(
                                name=metric.name,
                                value=float(metric.evaluator(output, params)),
                                unit=metric.unit,
                            )
                            for metric in metrics
                        )
                        results.append(
                            ExperimentCaseResult(
                                case=case,
                                output=output,
                                metrics=metric_values,
                            )
                        )
                except Exception as exc:
                    if failure_policy == "raise":
                        raise
                    error = f"{type(exc).__name__}: {exc}"
                    results.extend(
                        ExperimentCaseResult(
                            case=case,
                            output=None,
                            error=error,
                        )
                        for case in batch
                    )

            experiment = ExperimentResult(
                sweep=sweep,
                cases=tuple(results),
                name=name or sweep.name,
            )
            return BatchedExperimentResult(
                experiment=experiment,
                batch_size=batch_size,
                batch_count=batch_count,
                environment=(
                    capture_environment(registry)
                    if capture_environment_snapshot
                    else None
                ),
            )

        registry.register_semantic_type(
            "experiments.batched_result",
            BatchedExperimentResult,
        )
        registry.provide(
            "experiments.batched_result",
            BatchedExperimentResult,
        )
        registry.provide("experiments.run_sweep_batched", run_batched)
