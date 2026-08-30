from __future__ import annotations

from dataclasses import dataclass

from spectra.core.expressions import Expression


@dataclass(frozen=True)
class Interval:
    start: float
    end: float
    closed_start: bool = True
    closed_end: bool = True

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("interval end must be greater than start")

    @property
    def length(self) -> float:
        return self.end - self.start

    def contains(self, value: float) -> bool:
        left = value >= self.start if self.closed_start else value > self.start
        right = value <= self.end if self.closed_end else value < self.end
        return left and right


@dataclass(frozen=True)
class Function1D:
    expression: Expression
    domain: Interval
    variable: str = "x"

    def __post_init__(self) -> None:
        if self.variable not in self.expression.variables:
            raise ValueError(f"function variable '{self.variable}' is not declared by expression")

    def evaluate(self, x: float, **parameters: float) -> float:
        if not self.domain.contains(x):
            raise ValueError(f"x={x} lies outside function domain")
        values = dict(parameters)
        values[self.variable] = x
        return self.expression.evaluate(values)
