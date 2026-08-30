from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
from typing import Protocol, runtime_checkable

from spectra.core.expressions import Expression, compile_expression


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


@runtime_checkable
class RealFunction1D(Protocol):
    """Structural contract consumed by calculus and 1D visualization compilers."""

    domain: Interval

    def evaluate(self, x: float, **parameters: float) -> float:
        ...


@dataclass(frozen=True)
class CallableFunction1D:
    """Real-valued function backed by Python/native/plugin callable code."""

    evaluator: Callable[..., float]
    domain: Interval
    name: str = "callable_function"

    def evaluate(self, x: float, **parameters: float) -> float:
        if not self.domain.contains(x):
            raise ValueError(f"x={x} lies outside function domain")
        value = self.evaluator(float(x), **parameters)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("real function evaluator must return a real number")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("real function evaluator returned a non-finite value")
        return result


@dataclass(frozen=True)
class ComplexFunction1D:
    """Complex-valued function over a real one-dimensional domain."""

    evaluator: Callable[..., complex]
    domain: Interval
    name: str = "complex_function"

    def evaluate(self, x: float, **parameters: float) -> complex:
        if not self.domain.contains(x):
            raise ValueError(f"x={x} lies outside function domain")
        value = complex(self.evaluator(float(x), **parameters))
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("complex function evaluator returned a non-finite value")
        return value

    def real_part(self, *, name: str | None = None) -> CallableFunction1D:
        return CallableFunction1D(
            lambda x, **parameters: self.evaluate(x, **parameters).real,
            self.domain,
            name=name or f"{self.name}.real",
        )

    def imaginary_part(self, *, name: str | None = None) -> CallableFunction1D:
        return CallableFunction1D(
            lambda x, **parameters: self.evaluate(x, **parameters).imag,
            self.domain,
            name=name or f"{self.name}.imag",
        )

    def magnitude(self, *, name: str | None = None) -> CallableFunction1D:
        return CallableFunction1D(
            lambda x, **parameters: abs(self.evaluate(x, **parameters)),
            self.domain,
            name=name or f"{self.name}.magnitude",
        )

    def magnitude_squared(self, *, name: str | None = None) -> CallableFunction1D:
        return CallableFunction1D(
            lambda x, **parameters: abs(self.evaluate(x, **parameters)) ** 2,
            self.domain,
            name=name or f"{self.name}.magnitude_squared",
        )


@dataclass(frozen=True)
class RectDomain2D:
    x: Interval
    y: Interval

    def contains(self, x: float, y: float) -> bool:
        return self.x.contains(x) and self.y.contains(y)


@dataclass(frozen=True)
class Function1D:
    expression: Expression
    domain: Interval
    variable: str = "x"

    def __post_init__(self) -> None:
        if self.variable not in self.expression.variables:
            raise ValueError(f"function variable '{self.variable}' is not declared by expression")

    @classmethod
    def from_expression(
        cls,
        source: str,
        domain: Interval,
        *,
        variable: str = "x",
        parameters: tuple[str, ...] = (),
    ) -> "Function1D":
        expression = compile_expression(source, (variable, *parameters))
        return cls(expression=expression, domain=domain, variable=variable)

    def evaluate(self, x: float, **parameters: float) -> float:
        if not self.domain.contains(x):
            raise ValueError(f"x={x} lies outside function domain")
        values = dict(parameters)
        values[self.variable] = x
        return self.expression.evaluate(values)


@dataclass(frozen=True)
class Function2D:
    expression: Expression
    domain: RectDomain2D
    x_variable: str = "x"
    y_variable: str = "y"

    def __post_init__(self) -> None:
        if self.x_variable == self.y_variable:
            raise ValueError("Function2D variables must be distinct")
        for variable in (self.x_variable, self.y_variable):
            if variable not in self.expression.variables:
                raise ValueError(f"function variable '{variable}' is not declared by expression")

    @classmethod
    def from_expression(
        cls,
        source: str,
        domain: RectDomain2D,
        *,
        x_variable: str = "x",
        y_variable: str = "y",
        parameters: tuple[str, ...] = (),
    ) -> "Function2D":
        expression = compile_expression(
            source,
            (x_variable, y_variable, *parameters),
        )
        return cls(
            expression=expression,
            domain=domain,
            x_variable=x_variable,
            y_variable=y_variable,
        )

    def evaluate(self, x: float, y: float, **parameters: float) -> float:
        if not self.domain.contains(x, y):
            raise ValueError(f"point ({x}, {y}) lies outside function domain")
        values = dict(parameters)
        values[self.x_variable] = x
        values[self.y_variable] = y
        return self.expression.evaluate(values)
