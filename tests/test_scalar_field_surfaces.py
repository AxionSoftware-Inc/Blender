import math

import pytest

from spectra.core.primitives import Surface
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import (
    AxisSample,
    MathematicsDomain,
    ScalarField3D,
    ScalarFieldSurfaceView2D,
    TimeDependentScalarField3D,
    TimeScalarFieldSurfaceAnimation2D,
)


def test_static_scalar_field_compiles_to_surface() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    field = ScalarField3D(lambda position: position.x + position.y, name="plane")
    view = ScalarFieldSurfaceView2D(
        field=field,
        x=AxisSample(-1.0, 1.0, 3),
        y=AxisSample(-1.0, 1.0, 3),
        height_scale=2.0,
        name="plane-view",
    )
    scene = registry.compile_scene(view)

    assert len(scene.primitives) == 1
    surface = scene.primitives[0]
    assert isinstance(surface, Surface)
    assert len(surface.vertices) == 9
    assert len(surface.triangles) == 8
    assert surface.vertices[-1] == Vec3(1.0, 1.0, 4.0)


def test_time_scalar_field_animates_stable_surface_topology() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    field = TimeDependentScalarField3D(
        lambda position, time: math.sin(position.x + time) * math.cos(position.y),
        name="traveling-height",
    )
    animation = TimeScalarFieldSurfaceAnimation2D(
        field=field,
        x=AxisSample(0.0, math.pi, 4),
        y=AxisSample(0.0, math.pi, 3),
        start_time=0.0,
        end_time=math.pi / 2.0,
        temporal_samples=3,
        name="height-animation",
    )
    scene = registry.compile_scene(animation)

    assert len(scene.primitives) == 1
    surface = scene.primitives[0]
    assert isinstance(surface, Surface)
    assert scene.timeline.tracks[0].property_path == "vertices"

    start = scene.sample(0.0).get("height-animation")
    end = scene.sample(scene.timeline.duration).get("height-animation")
    assert isinstance(start, Surface)
    assert isinstance(end, Surface)
    assert start.triangles == end.triangles
    assert len(start.vertices) == len(end.vertices) == 12
    assert start.vertices != end.vertices
    assert end.vertices[0].z == pytest.approx(1.0)
