import pytest

from spectra.core.expressions import compile_expression
from spectra.domains import DomainRegistry
from spectra.domains.calculus import CalculusDomain
from spectra.domains.mathematics import Function1D, Interval, MathematicsDomain


def test_calculus_requires_mathematics_capability() -> None:
    registry = DomainRegistry()

    with pytest.raises(KeyError, match="mathematics.function1d"):
        registry.add_domain(CalculusDomain())


def test_calculus_composes_over_mathematics_domain() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())
    registry.add_domain(CalculusDomain())

    function = Function1D(
        expression=compile_expression("x*x", ("x",)),
        domain=Interval(-2.0, 2.0),
    )

    derivative_at = registry.require("calculus.derivative_at")
    tangent_at = registry.require("calculus.tangent_at")
    integrate = registry.require("calculus.integrate", min_version=2)

    assert derivative_at(function, 1.5) == pytest.approx(3.0, rel=1e-4)
    tangent = tangent_at(function, 1.5)
    assert tangent.y == pytest.approx(2.25)
    assert tangent.slope == pytest.approx(3.0, rel=1e-4)
    assert integrate(function, start=0.0, end=2.0) == pytest.approx(8.0 / 3.0, rel=1e-8)
    assert registry.capability_version("calculus.integrate") == 2
