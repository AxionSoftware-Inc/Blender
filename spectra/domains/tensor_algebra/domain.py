from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from spectra.domains.registry import DomainRegistry


@dataclass(frozen=True, slots=True)
class Tensor:
    """Dense real-valued tensor with arbitrary rank and row-major storage."""

    shape: tuple[int, ...]
    values: tuple[float, ...]
    name: str = "tensor"

    def __post_init__(self) -> None:
        if any(dimension < 1 for dimension in self.shape):
            raise ValueError("tensor dimensions must be positive")
        expected = math.prod(self.shape) if self.shape else 1
        if len(self.values) != expected:
            raise ValueError(
                f"tensor value count {len(self.values)} does not match shape {self.shape}"
            )
        normalized = tuple(float(value) for value in self.values)
        if not all(math.isfinite(value) for value in normalized):
            raise ValueError("tensor values must be finite")
        object.__setattr__(self, "values", normalized)
        if not self.name:
            raise ValueError("tensor name cannot be empty")

    @classmethod
    def scalar(cls, value: float, *, name: str = "scalar") -> "Tensor":
        return cls((), (float(value),), name=name)

    @classmethod
    def vector(cls, values: Iterable[float], *, name: str = "vector") -> "Tensor":
        data = tuple(float(value) for value in values)
        if not data:
            raise ValueError("tensor vector cannot be empty")
        return cls((len(data),), data, name=name)

    @classmethod
    def matrix(
        cls,
        rows: Iterable[Iterable[float]],
        *,
        name: str = "matrix",
    ) -> "Tensor":
        data = tuple(tuple(float(value) for value in row) for row in rows)
        if not data or not data[0]:
            raise ValueError("tensor matrix cannot be empty")
        width = len(data[0])
        if any(len(row) != width for row in data):
            raise ValueError("tensor matrix rows must have equal length")
        return cls(
            (len(data), width),
            tuple(value for row in data for value in row),
            name=name,
        )

    @property
    def rank(self) -> int:
        return len(self.shape)

    @property
    def size(self) -> int:
        return len(self.values)

    def _flat_index(self, indices: tuple[int, ...]) -> int:
        if len(indices) != self.rank:
            raise IndexError(
                f"tensor rank {self.rank} requires {self.rank} indices, got {len(indices)}"
            )
        flat = 0
        stride = 1
        for axis in range(self.rank - 1, -1, -1):
            index = indices[axis]
            dimension = self.shape[axis]
            if index < 0 or index >= dimension:
                raise IndexError(f"tensor index {index} out of bounds on axis {axis}")
            flat += index * stride
            stride *= dimension
        return flat

    def at(self, *indices: int) -> float:
        return self.values[self._flat_index(tuple(indices))]

    def with_name(self, name: str) -> "Tensor":
        return Tensor(self.shape, self.values, name=name)


def tensor_add(left: Tensor, right: Tensor, *, name: str = "sum") -> Tensor:
    if left.shape != right.shape:
        raise ValueError("tensor addition requires equal shapes")
    return Tensor(
        left.shape,
        tuple(a + b for a, b in zip(left.values, right.values, strict=True)),
        name=name,
    )


def tensor_scale(tensor: Tensor, scalar: float, *, name: str = "scaled") -> Tensor:
    factor = float(scalar)
    if not math.isfinite(factor):
        raise ValueError("tensor scale must be finite")
    return Tensor(
        tensor.shape,
        tuple(value * factor for value in tensor.values),
        name=name,
    )


def outer_product(left: Tensor, right: Tensor, *, name: str = "outer") -> Tensor:
    return Tensor(
        left.shape + right.shape,
        tuple(a * b for a in left.values for b in right.values),
        name=name,
    )


def _unravel_index(flat: int, shape: tuple[int, ...]) -> tuple[int, ...]:
    if not shape:
        return ()
    indices = [0] * len(shape)
    remainder = flat
    for axis in range(len(shape) - 1, -1, -1):
        dimension = shape[axis]
        indices[axis] = remainder % dimension
        remainder //= dimension
    return tuple(indices)


def permute_axes(
    tensor: Tensor,
    order: tuple[int, ...],
    *,
    name: str = "permuted",
) -> Tensor:
    if len(order) != tensor.rank or set(order) != set(range(tensor.rank)):
        raise ValueError("tensor axis permutation must contain each axis exactly once")
    new_shape = tuple(tensor.shape[axis] for axis in order)
    new_values = []
    for flat in range(math.prod(new_shape) if new_shape else 1):
        new_indices = _unravel_index(flat, new_shape)
        old_indices = [0] * tensor.rank
        for new_axis, old_axis in enumerate(order):
            old_indices[old_axis] = new_indices[new_axis]
        new_values.append(tensor.at(*old_indices))
    return Tensor(new_shape, tuple(new_values), name=name)


def contract(
    tensor: Tensor,
    axis_a: int,
    axis_b: int,
    *,
    name: str = "contracted",
) -> Tensor:
    """Contract two equal-sized axes of one tensor."""

    if tensor.rank < 2:
        raise ValueError("tensor contraction requires rank >= 2")
    if axis_a == axis_b:
        raise ValueError("tensor contraction axes must be distinct")
    if axis_a < 0:
        axis_a += tensor.rank
    if axis_b < 0:
        axis_b += tensor.rank
    if not (0 <= axis_a < tensor.rank and 0 <= axis_b < tensor.rank):
        raise IndexError("tensor contraction axis out of range")
    if tensor.shape[axis_a] != tensor.shape[axis_b]:
        raise ValueError("contracted tensor axes must have equal dimensions")

    contracted_axes = {axis_a, axis_b}
    remaining_axes = tuple(axis for axis in range(tensor.rank) if axis not in contracted_axes)
    result_shape = tuple(tensor.shape[axis] for axis in remaining_axes)
    result_size = math.prod(result_shape) if result_shape else 1
    contraction_size = tensor.shape[axis_a]
    result_values = []

    for flat in range(result_size):
        remaining_indices = _unravel_index(flat, result_shape)
        base = [0] * tensor.rank
        for axis, index in zip(remaining_axes, remaining_indices, strict=True):
            base[axis] = index
        total = 0.0
        for contracted_index in range(contraction_size):
            base[axis_a] = contracted_index
            base[axis_b] = contracted_index
            total += tensor.at(*base)
        result_values.append(total)

    return Tensor(result_shape, tuple(result_values), name=name)


def trace(tensor: Tensor, *, name: str = "trace") -> Tensor:
    if tensor.rank != 2:
        raise ValueError("tensor trace requires rank 2")
    return contract(tensor, 0, 1, name=name)


class TensorAlgebraDomain:
    name = "tensor_algebra"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("tensor.tensor", Tensor)
        registry.provide("tensor.tensor", Tensor)
        registry.provide("tensor.add", tensor_add)
        registry.provide("tensor.scale", tensor_scale)
        registry.provide("tensor.outer_product", outer_product)
        registry.provide("tensor.permute_axes", permute_axes)
        registry.provide("tensor.contract", contract)
        registry.provide("tensor.trace", trace)
