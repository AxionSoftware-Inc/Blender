from __future__ import annotations

import pytest

from spectra.domains import DomainRegistry
from spectra.domains.calculus import CalculusDomain
from spectra.domains.mathematics import Function1D, Interval, MathematicsDomain
from spectra.domains.probability import ContinuousProbabilityDomain


def test_continuous_probability_composes_math_and_calculus_domains() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        [
            ContinuousProbabilityDomain(),
            CalculusDomain(),
            MathematicsDomain(),
        ]
    )

    density = Function1D.from_expression("x", Interval(0.0, 1.0))
    make_distribution = registry.require("probability.continuous.make_distribution")
    probability_between = registry.require("probability.continuous.probability_between")
    cdf = registry.require("probability.continuous.cdf")

    distribution = make_distribution(density, name="triangular")

    assert distribution.normalization == pytest.approx(0.5, rel=1e-8)
    assert distribution.pdf(0.5) == pytest.approx(1.0)
    assert cdf(distribution, 0.5) == pytest.approx(0.25, rel=1e-7)
    assert probability_between(distribution, 0.25, 0.75) == pytest.approx(0.5, rel=1e-7)

    scene = registry.compile_scene(distribution)
    assert len(scene.primitives) == 1
    assert scene.primitives[0].kind == "polyline"


def test_continuous_probability_rejects_negative_density() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        [
            ContinuousProbabilityDomain(),
            CalculusDomain(),
            MathematicsDomain(),
        ]
    )
    density = Function1D.from_expression("x - 0.5", Interval(0.0, 1.0))
    make_distribution = registry.require("probability.continuous.make_distribution")

    with pytest.raises(ValueError, match="cannot be negative"):
        make_distribution(density)
