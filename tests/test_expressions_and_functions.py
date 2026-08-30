import math

import pytest

from spectra.compiler import compile_function1d
from spectra.core.expressions import ExpressionError, compile_expression
from spectra.core.primitives import Polyline
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import Function1D, Interval, MathematicsDomain


def test_expression_evaluates_declared_variables() -> None:
    expression = compile_expression("a * sin(x) + b", ("x", "a", "b"))
    value = expression.evaluate(x=math.pi / 2, a=2.0, b=3.0)
    assert value == pytest.approx(5.0)


def test_expression_rejects_unknown_symbols_and_unsafe_syntax() -> None:
    with pytest.raises(ExpressionError, match="unknown symbol"):
        compile_expression("secret + x", ("x",))

    with pytest.raises(ExpressionError):
        compile_expression("__import__('os').system('echo no')", ())


def test_interval_semantics() -> None:
    interval = Interval(-2.0, 3.0, closed_start=False)
    assert not interval.contains(-2.0)
    assert interval.contains(0.0)
    assert interval.contains(3.0)
    assert interval.length == pytest.approx(5.0)


def test_function1d_compiles_to_renderer_independent_polyline() -> None:
    expression = compile_expression("sin(x)", ("x",))
    function = Function1D(expression=expression, domain=Interval(-math.pi, math.pi))

    scene = compile_function1d(function, samples=9)

    assert len(scene.primitives) == 1
    curve = scene.primitives[0]
    assert isinstance(curve, Polyline)
    assert len(curve.points) == 9
    assert curve.points[4].x == pytest.approx(0.0)
    assert curve.points[4].y == pytest.approx(0.0)


def test_mathematics_domain_publishes_reusable_capabilities() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    compile_expr = registry.require("mathematics.compile_expression")
    interval_type = registry.require("mathematics.interval")
    function_type = registry.require("mathematics.function1d")

    expression = compile_expr("x*x", ("x",))
    function = function_type(expression, interval_type(-1.0, 1.0))

    assert function.evaluate(0.5) == pytest.approx(0.25)
