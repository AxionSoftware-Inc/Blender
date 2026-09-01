from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from itertools import product
import math
from typing import Any, Literal

from spectra.core.units import Unit
from spectra.domains.registry import DomainRegistry
from spectra.numerics import NumericalSolverImplementation


FailurePolicy = Literal["raise", "record"]
MetricEvaluator = Callable[[Any, Mapping[str, Any]], float]
CaseEvaluator = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class ParameterAxis:
    name: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("parameter axis name cannot be empty")
        if not self.values:
            raise ValueError("parameter axis requires at least one value")


@dataclass(frozen=True, slots=True)
class ParameterCase:
    case_id: str
    parameters: tuple[tuple[str, Any], ...]

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("parameter case_id cannot be empty")
        names = tuple(name for name, _value in self.parameters)
        if len(names) != len(set(names)):
            raise ValueError("parameter case contains duplicate parameter names")
        if any(not name for name in names):
            raise ValueError("parameter names cannot be empty")

    def as_dict(self) -> dict[str, Any]:
        return dict(self.parameters)


@dataclass(frozen=True, slots=True)
class ParameterSweep:
    axes: tuple[ParameterAxis, ...]
    name: str = "parameter_sweep"

    def __post_init__(self) -> None:
        if not self.axes:
            raise ValueError("parameter sweep requires at least one axis")
        names = tuple(axis.name for axis in self.axes)
        if len(names) != len(set(names)):
            raise ValueError("parameter sweep axis names must be unique")
        if not self.name:
            raise ValueError("parameter sweep name cannot be empty")

    @property
    def case_count(self) -> int:
        result = 1
        for axis in self.axes:
            result *= len(axis.values)
        return result

    def cases(self) -> tuple[ParameterCase, ...]:
        return tuple(
            ParameterCase(
                case_id=f"{self.name}.{index:04d}",
                parameters=tuple(
                    (axis.name, value)
                    for axis, value in zip(self.axes, values, strict=True)
                ),
            )
            for index, values in enumerate(product(*(axis.values for axis in self.axes)))
        )


@dataclass(frozen=True, slots=True)
class MetricSpec:
    name: str
    evaluator: MetricEvaluator
    unit: Unit | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("experiment metric name cannot be empty")
        if not callable(self.evaluator):
            raise TypeError("experiment metric evaluator must be callable")


@dataclass(frozen=True, slots=True)
class MetricValue:
    name: str
    value: float
    unit: Unit | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("metric value name cannot be empty")
        if not math.isfinite(float(self.value)):
            raise ValueError("metric value must be finite")
        object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True, slots=True)
class ExperimentCaseResult:
    case: ParameterCase
    output: Any | None
    metrics: tuple[MetricValue, ...] = ()
    error: str | None = None

    @property
    def successful(self) -> bool:
        return self.error is None

    def metric(self, name: str) -> MetricValue:
        for metric in self.metrics:
            if metric.name == name:
                return metric
        raise KeyError(f"unknown experiment metric: {name}")


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    sweep: ParameterSweep
    cases: tuple[ExperimentCaseResult, ...]
    name: str = "experiment"

    def __post_init__(self) -> None:
        if len(self.cases) != self.sweep.case_count:
            raise ValueError("experiment result case count must match parameter sweep")
        if not self.name:
            raise ValueError("experiment result name cannot be empty")

    @property
    def success_count(self) -> int:
        return sum(case.successful for case in self.cases)

    @property
    def failure_count(self) -> int:
        return len(self.cases) - self.success_count

    def metric_series(self, name: str) -> tuple[tuple[ParameterCase, MetricValue], ...]:
        return tuple(
            (case.case, case.metric(name))
            for case in self.cases
            if case.successful
        )


@dataclass(frozen=True, slots=True)
class SolverComparisonResult:
    role: str
    implementations: tuple[NumericalSolverImplementation, ...]
    experiment: ExperimentResult

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("solver comparison role cannot be empty")
        if not self.implementations:
            raise ValueError("solver comparison requires at least one implementation")


class ExperimentsDomain:
    """Generic deterministic parameter studies and numerical solver comparisons."""

    name = "experiments"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        def run_sweep(
            sweep: ParameterSweep,
            evaluator: CaseEvaluator,
            *,
            metrics: tuple[MetricSpec, ...] = (),
            failure_policy: FailurePolicy = "raise",
            name: str | None = None,
        ) -> ExperimentResult:
            if failure_policy not in {"raise", "record"}:
                raise ValueError("experiment failure_policy must be 'raise' or 'record'")
            metric_names = tuple(metric.name for metric in metrics)
            if len(metric_names) != len(set(metric_names)):
                raise ValueError("experiment metric names must be unique")

            results: list[ExperimentCaseResult] = []
            for case in sweep.cases():
                parameters = case.as_dict()
                try:
                    output = evaluator(parameters)
                    values = tuple(
                        MetricValue(
                            name=metric.name,
                            value=float(metric.evaluator(output, parameters)),
                            unit=metric.unit,
                        )
                        for metric in metrics
                    )
                    results.append(
                        ExperimentCaseResult(
                            case=case,
                            output=output,
                            metrics=values,
                        )
                    )
                except Exception as exc:
                    if failure_policy == "raise":
                        raise
                    results.append(
                        ExperimentCaseResult(
                            case=case,
                            output=None,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    )
            return ExperimentResult(
                sweep=sweep,
                cases=tuple(results),
                name=name or sweep.name,
            )

        def compare_solvers(
            role: str,
            problem: Any,
            *,
            implementation_ids: tuple[str, ...] | None = None,
            solver_kwargs: Mapping[str, Any] | None = None,
            metrics: tuple[MetricSpec, ...] = (),
            failure_policy: FailurePolicy = "record",
            name: str | None = None,
        ) -> SolverComparisonResult:
            available = registry.numerical_solver_implementations(role)
            if implementation_ids is None:
                selected = available
            else:
                requested = set(implementation_ids)
                selected = tuple(
                    implementation
                    for implementation in available
                    if implementation.implementation_id in requested
                )
                found = {implementation.implementation_id for implementation in selected}
                missing = tuple(sorted(requested - found))
                if missing:
                    raise KeyError(
                        "unknown numerical solver implementations for role "
                        f"{role}: {', '.join(missing)}"
                    )
            if not selected:
                raise ValueError("solver comparison requires at least one implementation")

            kwargs = dict(solver_kwargs or {})
            sweep = ParameterSweep(
                axes=(
                    ParameterAxis(
                        "implementation",
                        tuple(implementation.implementation_id for implementation in selected),
                    ),
                ),
                name=name or f"{role}.comparison",
            )

            def evaluate(parameters: Mapping[str, Any]) -> Any:
                implementation_id = str(parameters["implementation"])
                solver = registry.numerical_solver_for(role, implementation_id)
                return solver(problem, **kwargs)

            experiment = run_sweep(
                sweep,
                evaluate,
                metrics=metrics,
                failure_policy=failure_policy,
                name=name or f"{role}.comparison",
            )
            return SolverComparisonResult(
                role=role,
                implementations=selected,
                experiment=experiment,
            )

        registry.register_semantic_type("experiments.parameter_axis", ParameterAxis)
        registry.register_semantic_type("experiments.parameter_case", ParameterCase)
        registry.register_semantic_type("experiments.parameter_sweep", ParameterSweep)
        registry.register_semantic_type("experiments.metric_spec", MetricSpec)
        registry.register_semantic_type("experiments.metric_value", MetricValue)
        registry.register_semantic_type("experiments.case_result", ExperimentCaseResult)
        registry.register_semantic_type("experiments.result", ExperimentResult)
        registry.register_semantic_type("experiments.solver_comparison", SolverComparisonResult)
        registry.provide("experiments.parameter_axis", ParameterAxis)
        registry.provide("experiments.parameter_sweep", ParameterSweep)
        registry.provide("experiments.metric_spec", MetricSpec)
        registry.provide("experiments.run_sweep", run_sweep)
        registry.provide("experiments.compare_solvers", compare_solvers)
