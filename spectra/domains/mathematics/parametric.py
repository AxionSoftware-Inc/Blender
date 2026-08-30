from __future__ import annotations

from dataclasses import dataclass

from spectra.core.expressions import Expression, compile_expression
from spectra.core.types import Vec3
from spectra.domains.mathematics.functions import Interval, RectDomain2D


@dataclass(frozen=True)
class ParametricCurve3D:
    x_expression: Expression
    y_expression: Expression
    z_expression: Expression
    domain: Interval
    variable: str = "t"
    name: str = "parametric_curve"

    def __post_init__(self) -> None:
        for expression in (self.x_expression, self.y_expression, self.z_expression):
            if self.variable not in expression.variables:
                raise ValueError(
                    f"curve variable '{self.variable}' is not declared by all component expressions"
                )

    @classmethod
    def from_expressions(
        cls,
        x: str,
        y: str,
        z: str,
        domain: Interval,
        *,
        variable: str = "t",
        parameters: tuple[str, ...] = (),
        name: str = "parametric_curve",
    ) -> "ParametricCurve3D":
        variables = (variable, *parameters)
        return cls(
            x_expression=compile_expression(x, variables),
            y_expression=compile_expression(y, variables),
            z_expression=compile_expression(z, variables),
            domain=domain,
            variable=variable,
            name=name,
        )

    def evaluate(self, t: float, **parameters: float) -> Vec3:
        if not self.domain.contains(t):
            raise ValueError(f"t={t} lies outside curve domain")
        values = dict(parameters)
        values[self.variable] = t
        return Vec3(
            self.x_expression.evaluate(values),
            self.y_expression.evaluate(values),
            self.z_expression.evaluate(values),
        )


@dataclass(frozen=True)
class ParametricSurface3D:
    x_expression: Expression
    y_expression: Expression
    z_expression: Expression
    domain: RectDomain2D
    u_variable: str = "u"
    v_variable: str = "v"
    name: str = "parametric_surface"

    def __post_init__(self) -> None:
        if self.u_variable == self.v_variable:
            raise ValueError("surface parameters must be distinct")
        for expression in (self.x_expression, self.y_expression, self.z_expression):
            for variable in (self.u_variable, self.v_variable):
                if variable not in expression.variables:
                    raise ValueError(
                        f"surface parameter '{variable}' is not declared by all component expressions"
                    )

    @classmethod
    def from_expressions(
        cls,
        x: str,
        y: str,
        z: str,
        domain: RectDomain2D,
        *,
        u_variable: str = "u",
        v_variable: str = "v",
        parameters: tuple[str, ...] = (),
        name: str = "parametric_surface",
    ) -> "ParametricSurface3D":
        variables = (u_variable, v_variable, *parameters)
        return cls(
            x_expression=compile_expression(x, variables),
            y_expression=compile_expression(y, variables),
            z_expression=compile_expression(z, variables),
            domain=domain,
            u_variable=u_variable,
            v_variable=v_variable,
            name=name,
        )

    def evaluate(self, u: float, v: float, **parameters: float) -> Vec3:
        if not self.domain.contains(u, v):
            raise ValueError(f"parameters ({u}, {v}) lie outside surface domain")
        values = dict(parameters)
        values[self.u_variable] = u
        values[self.v_variable] = v
        return Vec3(
            self.x_expression.evaluate(values),
            self.y_expression.evaluate(values),
            self.z_expression.evaluate(values),
        )
