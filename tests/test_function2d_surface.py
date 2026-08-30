from __future__ import annotations

import pytest

from spectra.core.primitives import Surface
from spectra.core.serialization import scene_from_json, scene_to_json
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import Function2D, Interval, MathematicsDomain, RectDomain2D


def test_function2d_compiles_to_generic_surface() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    function = Function2D.from_expression(
        "x*x + y*y",
        RectDomain2D(Interval(-1.0, 1.0), Interval(-2.0, 2.0)),
    )
    scene = registry.compile_scene(function)

    surface = scene.get("surface")
    assert isinstance(surface, Surface)
    assert len(surface.vertices) == 48 * 48
    assert len(surface.triangles) == 2 * 47 * 47

    centerish = function.evaluate(0.0, 1.0)
    assert centerish == pytest.approx(1.0)


def test_surface_scene_is_backend_transportable_json() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())
    function = Function2D.from_expression(
        "sin(x) * cos(y)",
        RectDomain2D(Interval(-1.0, 1.0), Interval(-1.0, 1.0)),
    )

    original = registry.compile_scene(function)
    restored = scene_from_json(scene_to_json(original, indent=None))
    assert restored == original
