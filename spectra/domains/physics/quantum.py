from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from spectra.domains.linear_algebra import ComplexMatrixN, ComplexVectorN
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True)
class QuantumState:
    amplitudes: ComplexVectorN


@dataclass(frozen=True)
class QuantumObservable:
    name: str
    operator: ComplexMatrixN

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("quantum observable name cannot be empty")
        if not self.operator.is_square:
            raise ValueError("quantum observable operator must be square")


class QuantumDomain:
    name = "physics.quantum"
    version = "2"
    dependencies = (
        DomainDependency("linear_algebra.complex_vector"),
        DomainDependency("linear_algebra.normalize_complex"),
        DomainDependency("linear_algebra.complex_matrix", min_version=2),
        DomainDependency("linear_algebra.complex_matrix_vector_product", min_version=2),
        DomainDependency("linear_algebra.is_hermitian", min_version=2),
        DomainDependency("linear_algebra.complex_quadratic_form", min_version=2),
        DomainDependency("probability.discrete_distribution"),
    )

    def register(self, registry: DomainRegistry) -> None:
        vector_type = registry.require("linear_algebra.complex_vector")
        normalize = registry.require("linear_algebra.normalize_complex")
        matrix_type = registry.require("linear_algebra.complex_matrix", min_version=2)
        apply_matrix = registry.require(
            "linear_algebra.complex_matrix_vector_product",
            min_version=2,
        )
        is_hermitian = registry.require("linear_algebra.is_hermitian", min_version=2)
        quadratic_form = registry.require(
            "linear_algebra.complex_quadratic_form",
            min_version=2,
        )
        distribution_type = registry.require("probability.discrete_distribution")

        def make_state(amplitudes: Iterable[complex]) -> QuantumState:
            vector = vector_type(tuple(complex(value) for value in amplitudes))
            return QuantumState(normalize(vector))

        def measurement_distribution(state: QuantumState):
            pairs = tuple(
                (float(index), abs(amplitude) ** 2)
                for index, amplitude in enumerate(state.amplitudes.values)
            )
            return distribution_type.from_pairs(pairs)

        def make_observable(
            name: str,
            rows: Iterable[Iterable[complex]],
        ) -> QuantumObservable:
            operator = matrix_type.of(rows)
            if not is_hermitian(operator):
                raise ValueError("quantum observable must be represented by a Hermitian operator")
            return QuantumObservable(name=name, operator=operator)

        def apply_observable(
            observable: QuantumObservable,
            state: QuantumState,
        ) -> ComplexVectorN:
            if not is_hermitian(observable.operator):
                raise ValueError("quantum observable operator is not Hermitian")
            return apply_matrix(observable.operator, state.amplitudes)

        def expectation_value(
            state: QuantumState,
            observable: QuantumObservable,
        ) -> float:
            if not is_hermitian(observable.operator):
                raise ValueError("quantum observable operator is not Hermitian")
            value = quadratic_form(state.amplitudes, observable.operator)
            if abs(value.imag) > 1e-9:
                raise ValueError("Hermitian expectation value produced a non-real result")
            return float(value.real)

        registry.register_semantic_type("physics.quantum.state", QuantumState)
        registry.register_semantic_type("physics.quantum.observable", QuantumObservable)
        registry.provide("physics.quantum.make_state", make_state)
        registry.provide("physics.quantum.measurement_distribution", measurement_distribution)
        registry.provide("physics.quantum.make_observable", make_observable, version=2)
        registry.provide("physics.quantum.apply_observable", apply_observable, version=2)
        registry.provide("physics.quantum.expectation_value", expectation_value, version=2)
