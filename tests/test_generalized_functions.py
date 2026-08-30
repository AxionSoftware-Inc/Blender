import math

import pytest

from spectra.core.primitives import Polyline
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import CallableFunction1D, ComplexFunction1D, Interval


def test_callable_function_reuses_calculus_and_visualization_contracts() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["calculus"])

    function = CallableFunction1D(
        evaluator=lambda x: x * x,
        domain=Interval(-2.0, 2.0),
        name="square-callable",
    )
    derivative = registry.require("calculus.derivative_at")
    integrate = registry.require("calculus.integrate", min_version=3)

    assert derivative(function, 1.5) == pytest.approx(3.0, rel=1e-4)
    assert integrate(function) == pytest.approx(16.0 / 3.0, rel=1e-6)

    scene = registry.compile_scene(function)
    assert len(scene.primitives) == 1
    assert isinstance(scene.primitives[0], Polyline)


def test_complex_function_exposes_real_imaginary_and_density_views() -> None:
    function = ComplexFunction1D(
        evaluator=lambda x: complex(math.cos(x), math.sin(x)),
        domain=Interval(-math.pi, math.pi),
        name="phase",
    )

    assert function.evaluate(0.0) == pytest.approx(1.0 + 0.0j)
    assert function.real_part().evaluate(math.pi / 2.0) == pytest.approx(0.0, abs=1e-12)
    assert function.imaginary_part().evaluate(math.pi / 2.0) == pytest.approx(1.0)
    assert function.magnitude().evaluate(0.3) == pytest.approx(1.0)
    assert function.magnitude_squared().evaluate(-1.2) == pytest.approx(1.0)
