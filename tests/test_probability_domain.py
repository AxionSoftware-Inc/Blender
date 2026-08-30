import pytest

from spectra.domains import DomainRegistry
from spectra.domains.probability import DiscreteDistribution, ProbabilityDomain


def test_probability_domain_registers_without_calculus() -> None:
    registry = DomainRegistry()
    registry.add_domain(ProbabilityDomain())

    distribution_type = registry.require("probability.discrete_distribution")
    expectation = registry.require("probability.expectation")
    variance = registry.require("probability.variance")

    distribution = distribution_type.from_pairs(((0.0, 0.25), (2.0, 0.75)))

    assert isinstance(distribution, DiscreteDistribution)
    assert expectation(distribution) == pytest.approx(1.5)
    assert variance(distribution) == pytest.approx(0.75)


def test_distribution_rejects_invalid_probability_mass() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        DiscreteDistribution.from_pairs(((0.0, 0.2), (1.0, 0.2)))
