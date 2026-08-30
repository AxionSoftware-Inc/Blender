from __future__ import annotations

import math

from spectra.core.primitives import Polyline, Surface
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import (
    Interval,
    MathematicsDomain,
    ParametricCurve3D,
    ParametricSurface3D,
    RectDomain2D,
)


def test_parametric_curve_compiles_without_new_renderer_feature() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    helix = ParametricCurve3D.from_expressions(
        "cos(t)",
        "sin(t)",
        "t / 6",
        Interval(0.0, math.tau),
        name="helix",
    )
    scene = registry.compile_scene(helix)

    curve = scene.get("helix")
    assert isinstance(curve, Polyline)
    assert len(curve.points) == 128


def test_parametric_torus_reuses_generic_surface_primitive() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    torus = ParametricSurface3D.from_expressions(
        "(2 + 0.5*cos(v))*cos(u)",
        "(2 + 0.5*cos(v))*sin(u)",
        "0.5*sin(v)",
        RectDomain2D(Interval(0.0, math.tau), Interval(0.0, math.tau)),
        name="torus",
    )
    scene = registry.compile_scene(torus)

    surface = scene.get("torus")
    assert isinstance(surface, Surface)
    assert len(surface.vertices) == 48 * 48
    assert len(surface.triangles) == 2 * 47 * 47
