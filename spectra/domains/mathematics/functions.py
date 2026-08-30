from __future__ import annotations

from dataclasses import dataclass

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
