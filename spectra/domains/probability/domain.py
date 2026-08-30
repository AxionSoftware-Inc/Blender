from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from spectra.domains.registry import DomainRegistry


@dataclass(frozen=True)
class Outcome:
    value: float
    probability: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must lie in [0, 1]")


@dataclass(frozen=True)
class DiscreteDistribution:
    outcomes: tuple[Outcome, ...]

    def __post_init__(self) -> None:
        if not self.outcomes:
            raise ValueError("distribution must contain at least one outcome")
        total = sum(outcome.probability for outcome in self.outcomes)
        if abs(total - 1.0) > 1e-9:
            raise ValueError("distribution probabilities must sum to 1")

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[float, float]]) -> "DiscreteDistribution":
        return cls(tuple(Outcome(value, probability) for value, probability in pairs))


def expectation(distribution: DiscreteDistribution) -> float:
    return sum(outcome.value * outcome.probability for outcome in distribution.outcomes)


def variance(distribution: DiscreteDistribution) -> float:
    mean = expectation(distribution)
    return sum(
        ((outcome.value - mean) ** 2) * outcome.probability
        for outcome in distribution.outcomes
    )


class ProbabilityDomain:
    name = "probability"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.probability.visualization import compile_distribution_scene

        registry.register_semantic_type("probability.outcome", Outcome)
        registry.register_semantic_type("probability.discrete_distribution", DiscreteDistribution)
        registry.provide("probability.discrete_distribution", DiscreteDistribution)
        registry.provide("probability.expectation", expectation)
        registry.provide("probability.variance", variance)
        registry.register_visualization(DiscreteDistribution, compile_distribution_scene)
