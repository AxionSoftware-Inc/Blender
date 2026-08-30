from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.linear_algebra.domain import MatrixN, VectorN
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SymmetricEigenDecomposition:
    eigenvalues: tuple[float, ...]
    eigenvectors: tuple[VectorN, ...]
    converged: bool
    sweeps: int

    def __post_init__(self) -> None:
        if not self.eigenvalues:
            raise ValueError("eigendecomposition cannot be empty")
        if len(self.eigenvalues) != len(self.eigenvectors):
            raise ValueError("eigenvalue/eigenvector count mismatch")
        dimension = len(self.eigenvalues)
        if any(vector.dimension != dimension for vector in self.eigenvectors):
            raise ValueError("eigenvector dimension mismatch")
        if self.sweeps < 0:
            raise ValueError("eigensystem sweeps cannot be negative")


def symmetric_eigendecomposition(
    matrix: MatrixN,
    *,
    tolerance: float = 1e-12,
    max_sweeps: int = 64,
) -> SymmetricEigenDecomposition:
    """Jacobi eigensolver for real symmetric matrices.

    The implementation is a deterministic reference behind a capability
    boundary. Optimized native/LAPACK backends may replace it later.
    """

    if not matrix.is_square:
        raise ValueError("symmetric eigendecomposition requires a square matrix")
    if tolerance < 0.0 or not math.isfinite(tolerance):
        raise ValueError("eigensystem tolerance must be finite and non-negative")
    if max_sweeps < 1:
        raise ValueError("eigensystem max_sweeps must be >= 1")

    size = matrix.rows
    for row in range(size):
        for column in range(row + 1, size):
            if not math.isclose(
                matrix.values[row][column],
                matrix.values[column][row],
                rel_tol=1e-10,
                abs_tol=max(tolerance, 1e-14),
            ):
                raise ValueError("symmetric eigendecomposition requires a symmetric matrix")

    a = [list(row) for row in matrix.values]
    vectors = [
        [1.0 if row == column else 0.0 for column in range(size)]
        for row in range(size)
    ]
    converged = size == 1
    sweeps_used = 0

    for sweep in range(1, max_sweeps + 1):
        sweeps_used = sweep
        largest = 0.0
        pivot_p = 0
        pivot_q = 0
        for row in range(size):
            for column in range(row + 1, size):
                value = abs(a[row][column])
                if value > largest:
                    largest = value
                    pivot_p = row
                    pivot_q = column

        if largest <= tolerance:
            converged = True
            break

        p = pivot_p
        q = pivot_q
        app = a[p][p]
        aqq = a[q][q]
        apq = a[p][q]
        angle = 0.5 * math.atan2(2.0 * apq, aqq - app)
        cosine = math.cos(angle)
        sine = math.sin(angle)

        for index in range(size):
            if index in {p, q}:
                continue
            aip = a[index][p]
            aiq = a[index][q]
            new_ip = cosine * aip - sine * aiq
            new_iq = sine * aip + cosine * aiq
            a[index][p] = a[p][index] = new_ip
            a[index][q] = a[q][index] = new_iq

        a[p][p] = (
            cosine * cosine * app
            - 2.0 * sine * cosine * apq
            + sine * sine * aqq
        )
        a[q][q] = (
            sine * sine * app
            + 2.0 * sine * cosine * apq
            + cosine * cosine * aqq
        )
        a[p][q] = a[q][p] = 0.0

        for row in range(size):
            vip = vectors[row][p]
            viq = vectors[row][q]
            vectors[row][p] = cosine * vip - sine * viq
            vectors[row][q] = sine * vip + cosine * viq

    pairs = []
    for index in range(size):
        vector = VectorN.of(vectors[row][index] for row in range(size))
        magnitude = math.sqrt(sum(value * value for value in vector.values))
        if magnitude == 0.0:
            raise RuntimeError("Jacobi eigensolver produced zero eigenvector")
        normalized = VectorN.of(value / magnitude for value in vector.values)
        pairs.append((float(a[index][index]), normalized))

    pairs.sort(key=lambda item: item[0], reverse=True)
    return SymmetricEigenDecomposition(
        eigenvalues=tuple(value for value, _ in pairs),
        eigenvectors=tuple(vector for _, vector in pairs),
        converged=converged,
        sweeps=sweeps_used,
    )


class SymmetricEigensystemsDomain:
    name = "linear_algebra.symmetric_eigensystems"
    version = "1"
    dependencies = (
        DomainDependency("linear_algebra.matrix"),
        DomainDependency("linear_algebra.vector"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type(
            "linear_algebra.symmetric_eigendecomposition",
            SymmetricEigenDecomposition,
        )
        registry.provide(
            "linear_algebra.symmetric_eigendecomposition",
            symmetric_eigendecomposition,
        )
