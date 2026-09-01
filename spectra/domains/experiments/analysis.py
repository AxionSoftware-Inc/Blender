from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from spectra.domains.experiments.domain import ExperimentCaseResult, ExperimentResult, MetricValue
from spectra.domains.registry import DomainDependency, DomainRegistry


ObjectiveDirection = Literal["minimize", "maximize"]


@dataclass(frozen=True, slots=True)
class MetricObjective:
    metric: str
    direction: ObjectiveDirection = "minimize"

    def __post_init__(self) -> None:
        if not self.metric:
            raise ValueError("experiment objective metric cannot be empty")
        if self.direction not in {"minimize", "maximize"}:
            raise ValueError("experiment objective direction must be minimize or maximize")


@dataclass(frozen=True, slots=True)
class RankedExperimentCase:
    rank: int
    case: ExperimentCaseResult
    objective: MetricObjective
    normalized_value: float

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError("experiment rank must be >= 1")


@dataclass(frozen=True, slots=True)
class ParetoFront:
    objectives: tuple[MetricObjective, ...]
    cases: tuple[ExperimentCaseResult, ...]
    experiment_name: str

    def __post_init__(self) -> None:
        if not self.objectives:
            raise ValueError("Pareto front requires at least one objective")
        if not self.experiment_name:
            raise ValueError("Pareto front experiment_name cannot be empty")


def _si_metric(metric: MetricValue) -> float:
    if metric.unit is None:
        return metric.value
    return metric.unit.to_si(metric.value)


def _objective_value(case: ExperimentCaseResult, objective: MetricObjective) -> float:
    value = _si_metric(case.metric(objective.metric))
    return value if objective.direction == "minimize" else -value


def _dominates(
    left: ExperimentCaseResult,
    right: ExperimentCaseResult,
    objectives: tuple[MetricObjective, ...],
) -> bool:
    left_values = tuple(_objective_value(left, objective) for objective in objectives)
    right_values = tuple(_objective_value(right, objective) for objective in objectives)
    no_worse = all(left_value <= right_value for left_value, right_value in zip(left_values, right_values, strict=True))
    strictly_better = any(left_value < right_value for left_value, right_value in zip(left_values, right_values, strict=True))
    return no_worse and strictly_better


class ExperimentAnalysisDomain:
    """Deterministic ranking and multi-objective analysis of experiment metrics."""

    name = "experiments.analysis"
    version = "1"
    dependencies = (
        DomainDependency("experiments.result"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def rank_cases(
            experiment: ExperimentResult,
            objective: MetricObjective,
        ) -> tuple[RankedExperimentCase, ...]:
            successful = tuple(case for case in experiment.cases if case.successful)
            ordered = sorted(
                successful,
                key=lambda case: (
                    _objective_value(case, objective),
                    case.case.case_id,
                ),
            )
            return tuple(
                RankedExperimentCase(
                    rank=index + 1,
                    case=case,
                    objective=objective,
                    normalized_value=_objective_value(case, objective),
                )
                for index, case in enumerate(ordered)
            )

        def best_case(
            experiment: ExperimentResult,
            objective: MetricObjective,
        ) -> ExperimentCaseResult:
            ranking = rank_cases(experiment, objective)
            if not ranking:
                raise ValueError("experiment has no successful cases to rank")
            return ranking[0].case

        def pareto_front(
            experiment: ExperimentResult,
            objectives: tuple[MetricObjective, ...],
        ) -> ParetoFront:
            if not objectives:
                raise ValueError("Pareto analysis requires at least one objective")
            names = tuple(objective.metric for objective in objectives)
            if len(names) != len(set(names)):
                raise ValueError("Pareto objective metrics must be unique")
            successful = tuple(case for case in experiment.cases if case.successful)
            front = tuple(
                candidate
                for candidate in successful
                if not any(
                    _dominates(other, candidate, objectives)
                    for other in successful
                    if other is not candidate
                )
            )
            ordered = tuple(sorted(front, key=lambda case: case.case.case_id))
            return ParetoFront(
                objectives=objectives,
                cases=ordered,
                experiment_name=experiment.name,
            )

        registry.register_semantic_type("experiments.metric_objective", MetricObjective)
        registry.register_semantic_type("experiments.ranked_case", RankedExperimentCase)
        registry.register_semantic_type("experiments.pareto_front", ParetoFront)
        registry.provide("experiments.metric_objective", MetricObjective)
        registry.provide("experiments.rank_cases", rank_cases)
        registry.provide("experiments.best_case", best_case)
        registry.provide("experiments.pareto_front", pareto_front)
