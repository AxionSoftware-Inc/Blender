import math

import pytest

from spectra.domains import DomainRegistry
from spectra.domains.linear_algebra import LinearAlgebraDomain
from spectra.domains.physics import QuantumDomain
from spectra.domains.probability import ProbabilityDomain


def test_quantum_requires_linear_algebra_and_probability() -> None:
    registry = DomainRegistry()

    with pytest.raises(KeyError):
        registry.add_domain(QuantumDomain())


def test_quantum_composes_existing_domain_capabilities() -> None:
    registry = DomainRegistry()
    registry.add_domain(LinearAlgebraDomain())
    registry.add_domain(ProbabilityDomain())
    registry.add_domain(QuantumDomain())

    make_state = registry.require("physics.quantum.make_state")
    measurement_distribution = registry.require("physics.quantum.measurement_distribution")
    expectation = registry.require("probability.expectation")

    state = make_state((1.0 + 0j, 1.0j))
    distribution = measurement_distribution(state)

    assert sum(item.probability for item in distribution.outcomes) == pytest.approx(1.0)
    assert tuple(item.probability for item in distribution.outcomes) == pytest.approx((0.5, 0.5))
    assert expectation(distribution) == pytest.approx(0.5)
    assert abs(state.amplitudes.values[0]) == pytest.approx(1 / math.sqrt(2))
