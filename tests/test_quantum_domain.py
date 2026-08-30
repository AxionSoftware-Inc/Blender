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


def test_quantum_observable_reuses_versioned_linear_algebra_contracts() -> None:
    registry = DomainRegistry()
    registry.add_domains([QuantumDomain(), ProbabilityDomain(), LinearAlgebraDomain()])

    make_state = registry.require("physics.quantum.make_state")
    make_observable = registry.require("physics.quantum.make_observable", min_version=2)
    expectation_value = registry.require("physics.quantum.expectation_value", min_version=2)
    apply_observable = registry.require("physics.quantum.apply_observable", min_version=2)

    pauli_z = make_observable(
        "Pauli Z",
        (
            (1.0, 0.0),
            (0.0, -1.0),
        ),
    )
    zero_state = make_state((1.0, 0.0))
    plus_state = make_state((1.0, 1.0))

    assert expectation_value(zero_state, pauli_z) == pytest.approx(1.0)
    assert expectation_value(plus_state, pauli_z) == pytest.approx(0.0, abs=1e-12)
    applied = apply_observable(pauli_z, plus_state)
    assert applied.values[0].real == pytest.approx(1 / math.sqrt(2))
    assert applied.values[1].real == pytest.approx(-(1 / math.sqrt(2)))


def test_quantum_rejects_non_hermitian_observable() -> None:
    registry = DomainRegistry()
    registry.add_domains([QuantumDomain(), ProbabilityDomain(), LinearAlgebraDomain()])
    make_observable = registry.require("physics.quantum.make_observable", min_version=2)

    with pytest.raises(ValueError, match="Hermitian"):
        make_observable(
            "bad",
            (
                (0.0, 1.0),
                (0.0, 0.0),
            ),
        )
