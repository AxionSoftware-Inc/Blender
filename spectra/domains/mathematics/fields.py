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


@dataclass(frozen=True, slots=True)
class TimeDependentScalarField3D:
    """Renderer-neutral scalar field f(position, time).

    Time-dependent fields are mathematical semantics, not animation objects.
    Physics/PDE domains may snapshot them into ordinary ScalarField3D values or
    compile several snapshots into a Spectra Timeline.
    """

    evaluator: Callable[[Vec3, float], float]
    name: str = "time_scalar_field"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec3, time: float) -> float:
        return float(self.evaluator(position, float(time)))

    def at_time(self, time: float) -> ScalarField3D:
        sampled_time = float(time)
        return ScalarField3D(
            evaluator=lambda position: self.evaluate(position, sampled_time),
            name=f"{self.name}@{sampled_time:g}",
            output_unit=self.output_unit,
        )


@dataclass(frozen=True, slots=True)
class TimeDependentVectorField3D:
    """Renderer-neutral vector field F(position, time)."""

    evaluator: Callable[[Vec3, float], Vec3]
    name: str = "time_vector_field"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec3, time: float) -> Vec3:
        value = self.evaluator(position, float(time))
        if not isinstance(value, Vec3):
            raise TypeError("time-dependent vector field evaluator must return Vec3")
        return value

    def at_time(self, time: float) -> VectorField3D:
        sampled_time = float(time)
        return VectorField3D(
            evaluator=lambda position: self.evaluate(position, sampled_time),
            name=f"{self.name}@{sampled_time:g}",
            output_unit=self.output_unit,
        )
