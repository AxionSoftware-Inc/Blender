from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spectra.core.types import Vec2
from spectra.core.units import Unit


@dataclass(frozen=True, slots=True)
class ScalarField2D:
    evaluator: Callable[[Vec2], float]
    name: str = "scalar_field2d"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec2) -> float:
        return float(self.evaluator(position))


@dataclass(frozen=True, slots=True)
class VectorField2D:
    evaluator: Callable[[Vec2], Vec2]
    name: str = "vector_field2d"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec2) -> Vec2:
        value = self.evaluator(position)
        if not isinstance(value, Vec2):
            raise TypeError("2D vector field evaluator must return Vec2")
        return value


@dataclass(frozen=True, slots=True)
class TimeDependentScalarField2D:
    evaluator: Callable[[Vec2, float], float]
    name: str = "time_scalar_field2d"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec2, time: float) -> float:
        return float(self.evaluator(position, float(time)))

    def at_time(self, time: float) -> ScalarField2D:
        sampled_time = float(time)
        return ScalarField2D(
            evaluator=lambda position: self.evaluate(position, sampled_time),
            name=f"{self.name}@{sampled_time:g}",
            output_unit=self.output_unit,
        )


@dataclass(frozen=True, slots=True)
class TimeDependentVectorField2D:
    evaluator: Callable[[Vec2, float], Vec2]
    name: str = "time_vector_field2d"
    output_unit: Unit | None = None

    def evaluate(self, position: Vec2, time: float) -> Vec2:
        value = self.evaluator(position, float(time))
        if not isinstance(value, Vec2):
            raise TypeError("time-dependent 2D vector field evaluator must return Vec2")
        return value

    def at_time(self, time: float) -> VectorField2D:
        sampled_time = float(time)
        return VectorField2D(
            evaluator=lambda position: self.evaluate(position, sampled_time),
            name=f"{self.name}@{sampled_time:g}",
            output_unit=self.output_unit,
        )
