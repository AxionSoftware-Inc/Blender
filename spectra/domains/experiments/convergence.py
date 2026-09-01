from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
from typing import Any

from spectra.domains.registry import DomainDependency, DomainRegistry


ErrorEvaluator = Callable[[Any, Any], float]


@dataclass(frozen=True, slots=True)
class ConvergenceSample:
    steps: int
    step_size: float
    error: float

    def __post_init__(self) -> None:
        if self.steps < 1:
            raise ValueError("convergence sample steps must be >= 1")
        if not math.isfinite(self.step_size) or self.step_size <= 0.0:
            raise ValueError("convergence sample step_size must be finite and positive")
        if not math.isfinite(self.error) or self.error < 0.0:
            raise ValueError("convergence sample error must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class ConvergenceEstimate:
    coarse_steps: int
    fine_steps: int
    observed_order: float | None

    def __post_init__(self) -> None:
        if self.coarse_steps < 1 or self.fine_steps <= self.coarse_steps:
            raise ValueError("convergence estimate requires increasing positive step counts")
        if self.observed_order is not None and not math.isfinite(self.observed_order):
            raise ValueError("observed convergence order must be finite when defined")


@dataclass(frozen=True, slots=True)
class SolverConvergenceResult:
    role: str
    implementation_id: str
    samples: tuple[ConvergenceSample, ...]
    estimates: tuple[ConvergenceEstimate, ...]
    method_order: int | None = None
    name: str = "solver_convergence"

    def __post_init__(self) -> None:
        if not self.role or not self.implementation_id or not self.name:
            raise ValueError("solver convergence identifiers cannot be empty")
        if len(self.samples) < 2:
            raise ValueError("solver convergence requires at least two samples")
        if len(self.estimates) != len(self.samples) - 1:
            raise ValueError("solver convergence estimate count mismatch")
        if self.method_order is not None and self.method_order < 1:
            raise ValueError("solver convergence method_order must be >= 1")

    @property
    def finest(self) -> ConvergenceSample:
        return self.samples[-1]

    @property
    def latest_observed_order(self) -> float | None:
        return self.estimates[-1].observed_order

    def meets_order(self, *, tolerance: float = 0.5) -> bool | None:
        if tolerance < 0.0 or not math.isfinite(tolerance):
            raise ValueError("convergence-order tolerance must be finite and non-negative")
        observed = self.latest_observed_order
        if observed is None or self.method_order is None:
            return None
        return observed >= self.method_order - tolerance


def _observed_order(
    coarse_error: float,
    fine_error: float,
    coarse_step: float,
    fine_step: float,
) -> float | None:
    if coarse_error <= 0.0 or fine_error <= 0.0:
        return None
    error_ratio = coarse_error / fine_error
    step_ratio = coarse_step / fine_step
    if error_ratio <= 0.0 or step_ratio <= 1.0:
        return None
    return math.log(error_ratio) / math.log(step_ratio)


class ConvergenceExperimentsDomain:
    """Step-refinement convergence studies for interchangeable fixed-step solvers."""

    name = "experiments.convergence"
    version = "3"
    dependencies = (
        DomainDependency("ode.solver_role.first_order"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def run_solver_convergence(
            role: str,
            problem: Any,
            *,
            end_time: float,
            step_counts: tuple[int, ...],
            error: ErrorEvaluator,
            implementation_id: str | None = None,
            start_time: float | None = None,
            name: str | None = None,
        ) -> SolverConvergenceResult:
            if len(step_counts) < 2:
                raise ValueError("convergence study requires at least two step counts")
            steps = tuple(int(value) for value in step_counts)
            if any(value < 1 for value in steps):
                raise ValueError("convergence step counts must be positive")
            if any(fine <= coarse for coarse, fine in zip(steps, steps[1:])):
                raise ValueError("convergence step counts must be strictly increasing")
            inferred_start = getattr(problem, "initial_time", None)
            begin = float(
                start_time
                if start_time is not None
                else (inferred_start if inferred_start is not None else 0.0)
            )
            finish = float(end_time)
            if not math.isfinite(begin) or not math.isfinite(finish) or finish <= begin:
                raise ValueError("convergence time interval must be finite and positive")

            implementation = registry.numerical_solvers.implementation(role, implementation_id)
            if implementation.adaptive:
                raise ValueError(
                    "step-count convergence requires a fixed-step solver; "
                    f"'{implementation.implementation_id}' is adaptive"
                )
            samples = []
            for count in steps:
                solution = implementation.solver(problem, end_time=finish, steps=count)
                measured = float(error(solution, problem))
                if not math.isfinite(measured) or measured < 0.0:
                    raise ValueError("convergence error evaluator must return finite non-negative value")
                samples.append(
                    ConvergenceSample(
                        steps=count,
                        step_size=(finish - begin) / count,
                        error=measured,
                    )
                )

            estimates = tuple(
                ConvergenceEstimate(
                    coarse_steps=coarse.steps,
                    fine_steps=fine.steps,
                    observed_order=_observed_order(
                        coarse.error,
                        fine.error,
                        coarse.step_size,
                        fine.step_size,
                    ),
                )
                for coarse, fine in zip(samples, samples[1:])
            )
            return SolverConvergenceResult(
                role=role,
                implementation_id=implementation.implementation_id,
                samples=tuple(samples),
                estimates=estimates,
                method_order=implementation.effective_order,
                name=name or f"{role}.{implementation.implementation_id}.convergence",
            )

        registry.register_semantic_type("experiments.convergence_sample", ConvergenceSample)
        registry.register_semantic_type("experiments.convergence_estimate", ConvergenceEstimate)
        registry.register_semantic_type("experiments.solver_convergence", SolverConvergenceResult)
        registry.provide("experiments.convergence_sample", ConvergenceSample)
        registry.provide("experiments.convergence_estimate", ConvergenceEstimate)
        registry.provide("experiments.solver_convergence", SolverConvergenceResult)
        registry.provide("experiments.run_solver_convergence", run_solver_convergence)
