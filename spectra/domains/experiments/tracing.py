from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from spectra.domains.experiments.domain import (
    ExperimentCaseResult,
    ExperimentResult,
    MetricSpec,
    MetricValue,
    ParameterSweep,
)
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.numerics import NumericalRunRecord, TrackedNumericalResult
from spectra.reproducibility import ScientificEnvironmentSnapshot, capture_environment


T = TypeVar("T")
TracedCaseEvaluator = Callable[[Mapping[str, Any]], "TracedCaseOutput[Any]"]


@dataclass(frozen=True, slots=True)
class TracedCaseOutput(Generic[T]):
    output: T
    runs: tuple[NumericalRunRecord, ...] = ()

    def __post_init__(self) -> None:
        if any(not isinstance(run, NumericalRunRecord) for run in self.runs):
            raise TypeError("traced case runs must contain NumericalRunRecord values")

    @classmethod
    def from_tracked(
        cls,
        tracked: TrackedNumericalResult[T],
    ) -> "TracedCaseOutput[T]":
        return cls(output=tracked.result, runs=(tracked.run,))


@dataclass(frozen=True, slots=True)
class ExperimentCaseExecutionTrace:
    case_id: str
    runs: tuple[NumericalRunRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("experiment execution trace case_id cannot be empty")
        if any(not isinstance(run, NumericalRunRecord) for run in self.runs):
            raise TypeError("experiment execution trace requires NumericalRunRecord values")

    @property
    def solver_implementations(self) -> tuple[str, ...]:
        return tuple(
            run.implementation_id
            for run in self.runs
            if run.implementation_id is not None
        )


@dataclass(frozen=True, slots=True)
class TracedExperimentResult:
    experiment: ExperimentResult
    traces: tuple[ExperimentCaseExecutionTrace, ...]
    environment: ScientificEnvironmentSnapshot

    def __post_init__(self) -> None:
        if len(self.traces) != len(self.experiment.cases):
            raise ValueError("traced experiment trace count must match case count")
        expected = tuple(case.case.case_id for case in self.experiment.cases)
        actual = tuple(trace.case_id for trace in self.traces)
        if actual != expected:
            raise ValueError("traced experiment case IDs must align with experiment cases")

    @property
    def environment_fingerprint(self) -> str:
        return self.environment.fingerprint

    @property
    def numerical_run_count(self) -> int:
        return sum(len(trace.runs) for trace in self.traces)

    def trace_for(self, case_id: str) -> ExperimentCaseExecutionTrace:
        for trace in self.traces:
            if trace.case_id == case_id:
                return trace
        raise KeyError(f"unknown traced experiment case: {case_id}")


def traced_output(
    output: T,
    *tracked_results: TrackedNumericalResult[Any],
) -> TracedCaseOutput[T]:
    return TracedCaseOutput(
        output=output,
        runs=tuple(tracked.run for tracked in tracked_results),
    )


class ExperimentTracingDomain:
    """Per-case numerical execution provenance for deterministic experiments."""

    name = "experiments.tracing"
    version = "1"
    dependencies = (
        DomainDependency("experiments.parameter_sweep"),
        DomainDependency("experiments.metric_spec"),
        DomainDependency("experiments.result"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def run_sweep_traced(
            sweep: ParameterSweep,
            evaluator: TracedCaseEvaluator,
            *,
            metrics: tuple[MetricSpec, ...] = (),
            failure_policy: str = "raise",
            name: str | None = None,
        ) -> TracedExperimentResult:
            if failure_policy not in {"raise", "record"}:
                raise ValueError("traced experiment failure_policy must be 'raise' or 'record'")
            metric_names = tuple(metric.name for metric in metrics)
            if len(metric_names) != len(set(metric_names)):
                raise ValueError("traced experiment metric names must be unique")

            environment = capture_environment(registry)
            case_results: list[ExperimentCaseResult] = []
            traces: list[ExperimentCaseExecutionTrace] = []
            for case in sweep.cases():
                parameters = case.as_dict()
                try:
                    traced = evaluator(parameters)
                    if not isinstance(traced, TracedCaseOutput):
                        raise TypeError("traced experiment evaluator must return TracedCaseOutput")
                    metric_values = tuple(
                        MetricValue(
                            name=metric.name,
                            value=float(metric.evaluator(traced.output, parameters)),
                            unit=metric.unit,
                        )
                        for metric in metrics
                    )
                    case_results.append(
                        ExperimentCaseResult(
                            case=case,
                            output=traced.output,
                            metrics=metric_values,
                        )
                    )
                    traces.append(
                        ExperimentCaseExecutionTrace(
                            case_id=case.case_id,
                            runs=traced.runs,
                        )
                    )
                except Exception as exc:
                    if failure_policy == "raise":
                        raise
                    case_results.append(
                        ExperimentCaseResult(
                            case=case,
                            output=None,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    )
                    traces.append(ExperimentCaseExecutionTrace(case_id=case.case_id))

            experiment = ExperimentResult(
                sweep=sweep,
                cases=tuple(case_results),
                name=name or sweep.name,
            )
            return TracedExperimentResult(
                experiment=experiment,
                traces=tuple(traces),
                environment=environment,
            )

        registry.register_semantic_type("experiments.traced_case_output", TracedCaseOutput)
        registry.register_semantic_type(
            "experiments.case_execution_trace",
            ExperimentCaseExecutionTrace,
        )
        registry.register_semantic_type("experiments.traced_result", TracedExperimentResult)
        registry.provide("experiments.traced_case_output", TracedCaseOutput)
        registry.provide("experiments.case_execution_trace", ExperimentCaseExecutionTrace)
        registry.provide("experiments.traced_result", TracedExperimentResult)
        registry.provide("experiments.traced_output", traced_output)
        registry.provide("experiments.run_sweep_traced", run_sweep_traced)


__all__ = [
    "ExperimentCaseExecutionTrace",
    "ExperimentTracingDomain",
    "TracedCaseOutput",
    "TracedExperimentResult",
    "traced_output",
]
