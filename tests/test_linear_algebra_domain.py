from __future__ import annotations

import pytest

from spectra.domains import DomainRegistry
from spectra.domains.linear_algebra import (
    ComplexMatrixN,
    ComplexVectorN,
    LinearAlgebraDomain,
    complex_matrix_vector_product,
    complex_quadratic_form,
    is_hermitian,
)


def test_complex_matrix_operator_foundation() -> None:
    pauli_z = ComplexMatrixN.of(
        [
            [1.0, 0.0],
            [0.0, -1.0],
        ]
    )
    state = ComplexVectorN.of([1 / (2 ** 0.5), 1 / (2 ** 0.5)])

    assert is_hermitian(pauli_z)
    applied = complex_matrix_vector_product(pauli_z, state)
    assert applied.values[0].real == pytest.approx(2 ** -0.5)
    assert applied.values[1].real == pytest.approx(-(2 ** -0.5))
    assert complex_quadratic_form(state, pauli_z).real == pytest.approx(0.0, abs=1e-12)


def test_linear_algebra_publishes_versioned_matrix_contracts() -> None:
    registry = DomainRegistry()
    registry.add_domain(LinearAlgebraDomain())

    assert registry.capability_version("linear_algebra.complex_matrix") == 2
    assert registry.capability_version("linear_algebra.is_hermitian") == 2
    matrix_type = registry.require("linear_algebra.complex_matrix", min_version=2)
    assert matrix_type is ComplexMatrixN
