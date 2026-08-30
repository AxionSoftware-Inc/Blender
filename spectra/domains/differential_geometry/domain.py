from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math

from spectra.domains.linear_algebra import MatrixN, VectorN
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.tensor_algebra import Tensor


CoordinatePoint = tuple[float, ...]
MetricEvaluator = Callable[[CoordinatePoint], Tensor]


@dataclass(frozen=True, slots=True)
class MetricTensorField:
    """Symmetric non-degenerate metric tensor field on a coordinate chart.

    The metric may be positive definite or indefinite. This deliberately supports
    both Euclidean/Riemannian geometry and spacetime-style pseudo-Riemannian
    metrics without putting relativity concepts into the mathematics domain.
    """

    dimension: int
    evaluator: MetricEvaluator
    name: str = "metric"

    def __post_init__(self) -> None:
        if self.dimension < 1:
            raise ValueError("metric dimension must be positive")
        if not self.name:
            raise ValueError("metric name cannot be empty")

    def evaluate(self, point: Iterable[float]) -> Tensor:
        coordinates = tuple(float(value) for value in point)
        if len(coordinates) != self.dimension:
            raise ValueError("metric coordinate dimension mismatch")
        if not all(math.isfinite(value) for value in coordinates):
            raise ValueError("metric coordinates must be finite")
        tensor = self.evaluator(coordinates)
        if not isinstance(tensor, Tensor):
            raise TypeError("metric evaluator must return Tensor")
        if tensor.shape != (self.dimension, self.dimension):
            raise ValueError("metric evaluator must return a square rank-2 tensor")
        for row in range(self.dimension):
            for column in range(row + 1, self.dimension):
                if not math.isclose(
                    tensor.at(row, column),
                    tensor.at(column, row),
                    rel_tol=1e-9,
                    abs_tol=1e-12,
                ):
                    raise ValueError("metric tensor must be symmetric")
        return tensor

    @classmethod
    def constant(
        cls,
        matrix: Iterable[Iterable[float]],
        *,
        name: str = "constant_metric",
    ) -> "MetricTensorField":
        tensor = Tensor.matrix(matrix, name=name)
        if tensor.shape[0] != tensor.shape[1]:
            raise ValueError("constant metric must be square")
        dimension = tensor.shape[0]
        return cls(dimension, lambda _point: tensor, name=name)


def _tensor_to_matrix(metric: Tensor) -> MatrixN:
    if metric.rank != 2 or metric.shape[0] != metric.shape[1]:
        raise ValueError("metric tensor must be a square rank-2 tensor")
    size = metric.shape[0]
    return MatrixN.of(
        tuple(
            tuple(metric.at(row, column) for column in range(size))
            for row in range(size)
        )
    )


def _matrix_to_tensor(matrix: MatrixN, *, name: str) -> Tensor:
    return Tensor.matrix(matrix.values, name=name)


def metric_matrix(metric: MetricTensorField, point: Iterable[float]) -> MatrixN:
    return _tensor_to_matrix(metric.evaluate(point))


def inverse_metric(
    metric: MetricTensorField,
    point: Iterable[float],
    *,
    inverse_matrix: Callable[[MatrixN], MatrixN],
) -> Tensor:
    matrix = metric_matrix(metric, point)
    return _matrix_to_tensor(
        inverse_matrix(matrix),
        name=f"{metric.name}.inverse",
    )


def metric_inner_product(
    metric: MetricTensorField,
    point: Iterable[float],
    left: Iterable[float],
    right: Iterable[float],
) -> float:
    coordinates = tuple(float(value) for value in point)
    left_values = tuple(float(value) for value in left)
    right_values = tuple(float(value) for value in right)
    if len(left_values) != metric.dimension or len(right_values) != metric.dimension:
        raise ValueError("metric vector dimension mismatch")
    tensor = metric.evaluate(coordinates)
    return float(
        sum(
            left_values[row] * tensor.at(row, column) * right_values[column]
            for row in range(metric.dimension)
            for column in range(metric.dimension)
        )
    )


def lower_index(
    metric: MetricTensorField,
    point: Iterable[float],
    vector: Iterable[float],
) -> Tensor:
    values = tuple(float(value) for value in vector)
    if len(values) != metric.dimension:
        raise ValueError("vector dimension does not match metric")
    tensor = metric.evaluate(point)
    lowered = tuple(
        sum(tensor.at(row, column) * values[column] for column in range(metric.dimension))
        for row in range(metric.dimension)
    )
    return Tensor.vector(lowered, name="covector")


def raise_index(
    metric: MetricTensorField,
    point: Iterable[float],
    covector: Iterable[float],
    *,
    inverse_matrix: Callable[[MatrixN], MatrixN],
) -> Tensor:
    values = tuple(float(value) for value in covector)
    if len(values) != metric.dimension:
        raise ValueError("covector dimension does not match metric")
    inverse = inverse_matrix(metric_matrix(metric, point))
    raised = tuple(
        sum(inverse.values[row][column] * values[column] for column in range(metric.dimension))
        for row in range(metric.dimension)
    )
    return Tensor.vector(raised, name="vector")


def christoffel_symbols(
    metric: MetricTensorField,
    point: Iterable[float],
    *,
    inverse_matrix: Callable[[MatrixN], MatrixN],
    step: float = 1e-5,
) -> Tensor:
    """Numerical Levi-Civita connection coefficients Γ^i_jk.

    The implementation is a deterministic reference behind a capability
    boundary. Analytic/autodiff/native derivatives may replace it later.
    """

    coordinates = tuple(float(value) for value in point)
    if len(coordinates) != metric.dimension:
        raise ValueError("metric coordinate dimension mismatch")
    h = float(step)
    if not math.isfinite(h) or h <= 0.0:
        raise ValueError("Christoffel derivative step must be finite and positive")

    dimension = metric.dimension
    inverse = inverse_matrix(metric_matrix(metric, coordinates))

    # derivative[axis][row][column] = ∂_axis g_row,column
    derivative = [
        [[0.0 for _ in range(dimension)] for _ in range(dimension)]
        for _ in range(dimension)
    ]
    for axis in range(dimension):
        plus = list(coordinates)
        minus = list(coordinates)
        plus[axis] += h
        minus[axis] -= h
        plus_metric = metric.evaluate(tuple(plus))
        minus_metric = metric.evaluate(tuple(minus))
        for row in range(dimension):
            for column in range(dimension):
                derivative[axis][row][column] = (
                    plus_metric.at(row, column) - minus_metric.at(row, column)
                ) / (2.0 * h)

    values: list[float] = []
    for upper in range(dimension):
        for lower_a in range(dimension):
            for lower_b in range(dimension):
                coefficient = 0.0
                for contracted in range(dimension):
                    coefficient += 0.5 * inverse.values[upper][contracted] * (
                        derivative[lower_a][contracted][lower_b]
                        + derivative[lower_b][contracted][lower_a]
                        - derivative[contracted][lower_a][lower_b]
                    )
                values.append(coefficient)

    return Tensor(
        shape=(dimension, dimension, dimension),
        values=tuple(values),
        name=f"{metric.name}.christoffel",
    )


class DifferentialGeometryDomain:
    name = "differential_geometry"
    version = "1"
    dependencies = (
        DomainDependency("tensor.tensor"),
        DomainDependency("linear_algebra.matrix"),
        DomainDependency("linear_algebra.inverse", min_version=3),
    )

    def register(self, registry: DomainRegistry) -> None:
        inverse_matrix = registry.require("linear_algebra.inverse", min_version=3)

        registry.register_semantic_type("geometry.metric_tensor_field", MetricTensorField)
        registry.provide("geometry.metric_tensor_field", MetricTensorField)
        registry.provide("geometry.metric_matrix", metric_matrix)
        registry.provide(
            "geometry.inverse_metric",
            lambda metric, point: inverse_metric(
                metric,
                point,
                inverse_matrix=inverse_matrix,
            ),
        )
        registry.provide("geometry.metric_inner_product", metric_inner_product)
        registry.provide("geometry.lower_index", lower_index)
        registry.provide(
            "geometry.raise_index",
            lambda metric, point, covector: raise_index(
                metric,
                point,
                covector,
                inverse_matrix=inverse_matrix,
            ),
        )
        registry.provide(
            "geometry.christoffel_symbols",
            lambda metric, point, step=1e-5: christoffel_symbols(
                metric,
                point,
                inverse_matrix=inverse_matrix,
                step=step,
            ),
        )
