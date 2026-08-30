from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from spectra.domains.registry import DomainRegistry


@dataclass(frozen=True)
class VectorN:
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("vector must contain at least one component")

    @classmethod
    def of(cls, values: Iterable[float]) -> "VectorN":
        return cls(tuple(float(value) for value in values))

    @property
    def dimension(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class ComplexVectorN:
    values: tuple[complex, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("vector must contain at least one component")

    @classmethod
    def of(cls, values: Iterable[complex]) -> "ComplexVectorN":
        return cls(tuple(complex(value) for value in values))

    @property
    def dimension(self) -> int:
        return len(self.values)


def inner_product(left: VectorN, right: VectorN) -> float:
    if left.dimension != right.dimension:
        raise ValueError("vectors must have the same dimension")
    return sum(a * b for a, b in zip(left.values, right.values, strict=True))


def complex_inner_product(left: ComplexVectorN, right: ComplexVectorN) -> complex:
    if left.dimension != right.dimension:
        raise ValueError("vectors must have the same dimension")
    return sum(a.conjugate() * b for a, b in zip(left.values, right.values, strict=True))


def norm(vector: VectorN) -> float:
    return math.sqrt(inner_product(vector, vector))


def complex_norm(vector: ComplexVectorN) -> float:
    value = complex_inner_product(vector, vector)
    return math.sqrt(max(value.real, 0.0))


def normalize(vector: VectorN) -> VectorN:
    magnitude = norm(vector)
    if magnitude == 0.0:
        raise ValueError("zero vector cannot be normalized")
    return VectorN(tuple(value / magnitude for value in vector.values))


def normalize_complex(vector: ComplexVectorN) -> ComplexVectorN:
    magnitude = complex_norm(vector)
    if magnitude == 0.0:
        raise ValueError("zero vector cannot be normalized")
    return ComplexVectorN(tuple(value / magnitude for value in vector.values))


class LinearAlgebraDomain:
    name = "linear_algebra"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("linear_algebra.vector", VectorN)
        registry.register_semantic_type("linear_algebra.complex_vector", ComplexVectorN)
        registry.provide("linear_algebra.vector", VectorN)
        registry.provide("linear_algebra.complex_vector", ComplexVectorN)
        registry.provide("linear_algebra.inner_product", inner_product)
        registry.provide("linear_algebra.complex_inner_product", complex_inner_product)
        registry.provide("linear_algebra.norm", norm)
        registry.provide("linear_algebra.complex_norm", complex_norm)
        registry.provide("linear_algebra.normalize", normalize)
        registry.provide("linear_algebra.normalize_complex", normalize_complex)
