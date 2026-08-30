import math

import pytest

from spectra.core.expressions import compile_expression
from spectra.core.primitives import Point, Polyline, TextLabel
from spectra.domains.calculus.visualization import compile_tangent_scene
from spectra.domains.mathematics import Function1D, Interval
from spectra.domains.probability import DiscreteDistribution
from spectra.domains.probability.visualization import compile_distribution_scene


def test_tangent_scene_uses_generic_primitives() -> None:
    function = Function1D(
        expression=compile_expression("x*x", ("x",)),
        domain=Interval(-2.0, 2.0),
    )

    scene = compile_tangent_scene(function, 1.0, samples=9)

    assert isinstance(scene.get("function"), Polyline)
    marker = scene.get("tangent.point")
    tangent_line = scene.get("tangent.line")
    assert isinstance(marker, Point)
    assert isinstance(tangent_line, Polyline)
    assert marker.position.y == pytest.approx(1.0)
    slope = (
        tangent_line.points[1].y - tangent_line.points[0].y
    ) / (
        tangent_line.points[1].x - tangent_line.points[0].x
    )
    assert slope == pytest.approx(2.0, rel=1e-4)


def test_probability_scene_is_renderer_independent() -> None:
    distribution = DiscreteDistribution.from_pairs(((0.0, 0.25), (1.0, 0.75)))
    scene = compile_distribution_scene(distribution)

    assert len(scene.primitives) == 4
    assert isinstance(scene.get("probability.stem.0"), Polyline)
    assert isinstance(scene.get("probability.label.1"), TextLabel)
    assert scene.get("probability.stem.1").points[1].y == pytest.approx(0.75)
