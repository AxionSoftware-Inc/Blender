from __future__ import annotations

from dataclasses import dataclass

from spectra.domains.linear_algebra import ComplexVectorN
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True)
class QuantumState:
    amplitudes: ComplexVectorN


class QuantumDomain:
    name = "physics.quantum"
    version = "1"
    dependencies = (
        DomainDependency("linear_algebra.complex_vector"),
        DomainDependency("linear_algebra.normalize_complex"),
        DomainDependency("probability.discrete_distribution"),
    )

    def register(self, registry: DomainRegistry) -> None:
        vector_type = registry.require("linear_algebra.complex_vector")
        normalize = registry.require("linear_algebra.normalize_complex")
        distribution_type = registry.require("probability.discrete_distribution")

        def make_state(amplitudes: tuple[complex, ...]) -> QuantumState:
            vector = vector_type(amplitudes)
            return QuantumState(normalize(vector))

        def measurement_distribution(state: QuantumState):
            pairs = tuple(
                (float(index), abs(amplitude) ** 2)
                for index, amplitude in enumerate(state.amplitudes.values)
            )
            return distribution_type.from_pairs(pairs)

        registry.register_semantic_type("physics.quantum.state", QuantumState)
        registry.provide("physics.quantum.make_state", make_state)
        registry.provide("physics.quantum.measurement_distribution", measurement_distribution)
