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


@dataclass(frozen=True)
class MatrixN:
    values: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if not self.values or not self.values[0]:
            raise ValueError("matrix must contain at least one row and column")
        width = len(self.values[0])
        if any(len(row) != width for row in self.values):
            raise ValueError("matrix rows must have equal lengths")
        normalized = tuple(tuple(float(value) for value in row) for row in self.values)
        if not all(math.isfinite(value) for row in normalized for value in row):
            raise ValueError("matrix values must be finite")
        object.__setattr__(self, "values", normalized)

    @classmethod
    def of(cls, rows: Iterable[Iterable[float]]) -> "MatrixN":
        return cls(tuple(tuple(float(value) for value in row) for row in rows))

    @property
    def rows(self) -> int:
        return len(self.values)

    @property
    def columns(self) -> int:
        return len(self.values[0])

    @property
    def shape(self) -> tuple[int, int]:
        return (self.rows, self.columns)

    @property
    def is_square(self) -> bool:
        return self.rows == self.columns


@dataclass(frozen=True)
class ComplexMatrixN:
    values: tuple[tuple[complex, ...], ...]

    def __post_init__(self) -> None:
        if not self.values or not self.values[0]:
            raise ValueError("matrix must contain at least one row and column")
        width = len(self.values[0])
        if any(len(row) != width for row in self.values):
            raise ValueError("matrix rows must have equal lengths")
        normalized = tuple(tuple(complex(value) for value in row) for row in self.values)
        if not all(
            math.isfinite(value.real) and math.isfinite(value.imag)
            for row in normalized
            for value in row
        ):
            raise ValueError("complex matrix values must be finite")
        object.__setattr__(self, "values", normalized)

    @classmethod
    def of(cls, rows: Iterable[Iterable[complex]]) -> "ComplexMatrixN":
        return cls(tuple(tuple(complex(value) for value in row) for row in rows))

    @property
    def rows(self) -> int:
        return len(self.values)

    @property
    def columns(self) -> int:
        return len(self.values[0])

    @property
    def shape(self) -> tuple[int, int]:
        return (self.rows, self.columns)

    @property
    def is_square(self) -> bool:
        return self.rows == self.columns


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


def matrix_vector_product(matrix: MatrixN, vector: VectorN) -> VectorN:
    if matrix.columns != vector.dimension:
        raise ValueError("matrix columns must match vector dimension")
    return VectorN(
        tuple(
            sum(value * component for value, component in zip(row, vector.values, strict=True))
            for row in matrix.values
        )
    )


def complex_matrix_vector_product(
    matrix: ComplexMatrixN,
    vector: ComplexVectorN,
) -> ComplexVectorN:
    if matrix.columns != vector.dimension:
        raise ValueError("matrix columns must match vector dimension")
    return ComplexVectorN(
        tuple(
            sum(value * component for value, component in zip(row, vector.values, strict=True))
            for row in matrix.values
        )
    )


def transpose(matrix: MatrixN) -> MatrixN:
    return MatrixN(
        tuple(
            tuple(matrix.values[row][column] for row in range(matrix.rows))
            for column in range(matrix.columns)
        )
    )


def conjugate_transpose(matrix: ComplexMatrixN) -> ComplexMatrixN:
    return ComplexMatrixN(
        tuple(
            tuple(matrix.values[row][column].conjugate() for row in range(matrix.rows))
            for column in range(matrix.columns)
        )
    )


def determinant(matrix: MatrixN, *, tolerance: float = 1e-12) -> float:
    """Determinant through pivoted Gaussian elimination."""
    if not matrix.is_square:
        raise ValueError("determinant requires a square matrix")
    if tolerance < 0.0:
        raise ValueError("tolerance cannot be negative")

    work = [list(row) for row in matrix.values]
    sign = 1.0
    result = 1.0
    size = matrix.rows
    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(work[row][pivot_column]),
        )
        pivot = work[pivot_row][pivot_column]
        if abs(pivot) <= tolerance:
            return 0.0
        if pivot_row != pivot_column:
            work[pivot_column], work[pivot_row] = work[pivot_row], work[pivot_column]
            sign *= -1.0
        pivot = work[pivot_column][pivot_column]
        result *= pivot
        for row in range(pivot_column + 1, size):
            factor = work[row][pivot_column] / pivot
            for column in range(pivot_column + 1, size):
                work[row][column] -= factor * work[pivot_column][column]
    return float(sign * result)


def inverse(matrix: MatrixN, *, tolerance: float = 1e-12) -> MatrixN:
    """Inverse through pivoted Gauss-Jordan elimination."""
    if not matrix.is_square:
        raise ValueError("matrix inverse requires a square matrix")
    if tolerance < 0.0:
        raise ValueError("tolerance cannot be negative")

    size = matrix.rows
    work = [
        list(matrix.values[row])
        + [1.0 if row == column else 0.0 for column in range(size)]
        for row in range(size)
    ]

    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(work[row][pivot_column]),
        )
        if abs(work[pivot_row][pivot_column]) <= tolerance:
            raise ValueError("matrix is singular and cannot be inverted")
        if pivot_row != pivot_column:
            work[pivot_column], work[pivot_row] = work[pivot_row], work[pivot_column]

        pivot = work[pivot_column][pivot_column]
        work[pivot_column] = [value / pivot for value in work[pivot_column]]
        for row in range(size):
            if row == pivot_column:
                continue
            factor = work[row][pivot_column]
            if factor == 0.0:
                continue
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[pivot_column], strict=True)
            ]

    return MatrixN(
        tuple(tuple(row[size:]) for row in work)
    )


def complex_determinant(
    matrix: ComplexMatrixN,
    *,
    tolerance: float = 1e-12,
) -> complex:
    if not matrix.is_square:
        raise ValueError("determinant requires a square matrix")
    if tolerance < 0.0:
        raise ValueError("tolerance cannot be negative")

    work = [list(row) for row in matrix.values]
    sign = 1.0 + 0.0j
    result = 1.0 + 0.0j
    size = matrix.rows
    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(work[row][pivot_column]),
        )
        pivot = work[pivot_row][pivot_column]
        if abs(pivot) <= tolerance:
            return 0.0 + 0.0j
        if pivot_row != pivot_column:
            work[pivot_column], work[pivot_row] = work[pivot_row], work[pivot_column]
            sign *= -1.0
        pivot = work[pivot_column][pivot_column]
        result *= pivot
        for row in range(pivot_column + 1, size):
            factor = work[row][pivot_column] / pivot
            for column in range(pivot_column + 1, size):
                work[row][column] -= factor * work[pivot_column][column]
    return sign * result


def complex_inverse(
    matrix: ComplexMatrixN,
    *,
    tolerance: float = 1e-12,
) -> ComplexMatrixN:
    if not matrix.is_square:
        raise ValueError("matrix inverse requires a square matrix")
    if tolerance < 0.0:
        raise ValueError("tolerance cannot be negative")

    size = matrix.rows
    work = [
        list(matrix.values[row])
        + [1.0 + 0.0j if row == column else 0.0 + 0.0j for column in range(size)]
        for row in range(size)
    ]
    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(work[row][pivot_column]),
        )
        if abs(work[pivot_row][pivot_column]) <= tolerance:
            raise ValueError("matrix is singular and cannot be inverted")
        if pivot_row != pivot_column:
            work[pivot_column], work[pivot_row] = work[pivot_row], work[pivot_column]

        pivot = work[pivot_column][pivot_column]
        work[pivot_column] = [value / pivot for value in work[pivot_column]]
        for row in range(size):
            if row == pivot_column:
                continue
            factor = work[row][pivot_column]
            if factor == 0.0:
                continue
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[pivot_column], strict=True)
            ]
    return ComplexMatrixN(tuple(tuple(row[size:]) for row in work))


def is_hermitian(matrix: ComplexMatrixN, *, tolerance: float = 1e-9) -> bool:
    if tolerance < 0.0:
        raise ValueError("tolerance cannot be negative")
    if not matrix.is_square:
        return False
    adjoint = conjugate_transpose(matrix)
    return all(
        abs(left - right) <= tolerance
        for left_row, right_row in zip(matrix.values, adjoint.values, strict=True)
        for left, right in zip(left_row, right_row, strict=True)
    )


def complex_quadratic_form(vector: ComplexVectorN, matrix: ComplexMatrixN) -> complex:
    if not matrix.is_square or matrix.columns != vector.dimension:
        raise ValueError("quadratic form requires square matrix matching vector dimension")
    return complex_inner_product(vector, complex_matrix_vector_product(matrix, vector))


def complex_identity(size: int) -> ComplexMatrixN:
    if size < 1:
        raise ValueError("identity matrix size must be positive")
    return ComplexMatrixN(
        tuple(
            tuple(1.0 + 0.0j if row == column else 0.0 + 0.0j for column in range(size))
            for row in range(size)
        )
    )


class LinearAlgebraDomain:
    name = "linear_algebra"
    version = "3"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("linear_algebra.vector", VectorN)
        registry.register_semantic_type("linear_algebra.complex_vector", ComplexVectorN)
        registry.register_semantic_type("linear_algebra.matrix", MatrixN)
        registry.register_semantic_type("linear_algebra.complex_matrix", ComplexMatrixN)

        registry.provide("linear_algebra.vector", VectorN)
        registry.provide("linear_algebra.complex_vector", ComplexVectorN)
        registry.provide("linear_algebra.matrix", MatrixN)
        registry.provide("linear_algebra.complex_matrix", ComplexMatrixN, version=2)
        registry.provide("linear_algebra.inner_product", inner_product)
        registry.provide("linear_algebra.complex_inner_product", complex_inner_product)
        registry.provide("linear_algebra.norm", norm)
        registry.provide("linear_algebra.complex_norm", complex_norm)
        registry.provide("linear_algebra.normalize", normalize)
        registry.provide("linear_algebra.normalize_complex", normalize_complex)
        registry.provide("linear_algebra.matrix_vector_product", matrix_vector_product)
        registry.provide(
            "linear_algebra.complex_matrix_vector_product",
            complex_matrix_vector_product,
            version=2,
        )
        registry.provide("linear_algebra.transpose", transpose, version=3)
        registry.provide("linear_algebra.determinant", determinant, version=3)
        registry.provide("linear_algebra.inverse", inverse, version=3)
        registry.provide("linear_algebra.complex_determinant", complex_determinant, version=3)
        registry.provide("linear_algebra.complex_inverse", complex_inverse, version=3)
        registry.provide("linear_algebra.conjugate_transpose", conjugate_transpose, version=2)
        registry.provide("linear_algebra.is_hermitian", is_hermitian, version=2)
        registry.provide(
            "linear_algebra.complex_quadratic_form",
            complex_quadratic_form,
            version=2,
        )
        registry.provide("linear_algebra.complex_identity", complex_identity, version=2)
