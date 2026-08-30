from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import Unit
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.tensor_algebra import Tensor


TensorFieldEvaluator3D = Callable[[Vec3], Tensor]
TimeTensorFieldEvaluator3D = Callable[[Vec3, float], Tensor]


@dataclass(frozen=True, slots=True)
class TensorField3D:
    evaluator: TensorFieldEvaluator3D
    shape: tuple[int, ...]
    name: str = "tensor_field3d"
    output_unit: Unit | None = None

    def __post_init__(self) -> None:
        if any(dimension < 1 for dimension in self.shape):
            raise ValueError("tensor field shape dimensions must be positive")
        if not self.name:
            raise ValueError("tensor field name cannot be empty")

    def evaluate(self, position: Vec3) -> Tensor:
        value = self.evaluator(position)
        if not isinstance(value, Tensor):
            raise TypeError("tensor field evaluator must return Tensor")
        if value.shape != self.shape:
            raise ValueError("tensor field evaluator returned unexpected tensor shape")
        return value


@dataclass(frozen=True, slots=True)
class TimeDependentTensorField3D:
    evaluator: TimeTensorFieldEvaluator3D
    shape: tuple[int, ...]
    name: str = "time_tensor_field3d"
    output_unit: Unit | None = None

    def __post_init__(self) -> None:
        if any(dimension < 1 for dimension in self.shape):
            raise ValueError("time tensor field shape dimensions must be positive")
        if not self.name:
            raise ValueError("time tensor field name cannot be empty")

    def evaluate(self, position: Vec3, time: float) -> Tensor:
        sampled_time = float(time)
        if not math.isfinite(sampled_time):
            raise ValueError("tensor field sample time must be finite")
        value = self.evaluator(position, sampled_time)
        if not isinstance(value, Tensor):
            raise TypeError("time tensor field evaluator must return Tensor")
        if value.shape != self.shape:
            raise ValueError("time tensor field evaluator returned unexpected tensor shape")
        return value

    def at_time(self, time: float) -> TensorField3D:
        sampled_time = float(time)
        if not math.isfinite(sampled_time):
            raise ValueError("tensor field sample time must be finite")
        return TensorField3D(
            evaluator=lambda position: self.evaluate(position, sampled_time),
            shape=self.shape,
            name=f"{self.name}@{sampled_time:g}",
            output_unit=self.output_unit,
        )


class TensorFieldsDomain:
    name = "tensor_fields"
    version = "1"
    dependencies = (DomainDependency("tensor.tensor"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("tensor.field3d", TensorField3D)
        registry.register_semantic_type("tensor.time_field3d", TimeDependentTensorField3D)
        registry.provide("tensor.field3d", TensorField3D)
        registry.provide("tensor.time_field3d", TimeDependentTensorField3D)
