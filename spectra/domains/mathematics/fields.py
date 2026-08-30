from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from spectra.core.types import Vec3
from spectra.core.units import Unit


@dataclass(frozen=True, slots=True)
class AxisSample:
    start: float
    end: float
    count: int

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError("axis sample count must be >= 1")
        if self.end < self.start:
            raise ValueError("axis sample end must be >= start")

    def values(self) -> tuple[float, ...]:
        if self.count == 1:
            return ((self.start + self.end) * 0.5,)
        step = (self.end - self.start) / (self.count - 1)
        return tuple(self.start + step * index for index in range(self.count))


@dataclass(frozen=True, slots=True)
class RegularGrid3D:
    x: AxisSample
    y: AxisSample
    z: AxisSample

    def points(self) -> Iterator[Vec3]:
        for x in self.x.values():
            for y in self.y.values():
                for z in self.z.values():
                    yield Vec3(x, y, z)


@dataclass(frozen=True, slots=True)
class ScalarField3D:
    evaluator: Callable[[Vec3], float]
    name: str = "scalar_field"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec3) -> float:
        return float(self.evaluator(position))


@dataclass(frozen=True, slots=True)
class VectorField3D:
    evaluator: Callable[[Vec3], Vec3]
    name: str = "vector_field"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec3) -> Vec3:
        value = self.evaluator(position)
        if not isinstance(value, Vec3):
            raise TypeError("vector field evaluator must return Vec3")
        return value
