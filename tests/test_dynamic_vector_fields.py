import math

import pytest

from spectra.core.primitives import VectorGlyphSet
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import (
    AxisSample,
    MathematicsDomain,
    RegularGrid3D,
    TimeDependentVectorField3D,
    TimeVectorFieldAnimation3D,
)


def test_time_dependent_vector_field_can_snapshot_without_renderer() -> None:
    field = TimeDependentVectorField3D(
        lambda position, time: Vec3(position.x * math.cos(time), position.x * math.sin(time), 0.0),
        name="rotating",
    )
    snapshot = field.at_time(math.pi / 2.0)
    value = snapshot.evaluate(Vec3(2.0, 0.0, 0.0))

    assert value.x == pytest.approx(0.0, abs=1e-10)
    assert value.y == pytest.approx(2.0)


def test_time_vector_field_animation_compiles_to_one_batched_glyph_set() -> None:
    registry = DomainRegistry()
    registry.add_domain(MathematicsDomain())

    field = TimeDependentVectorField3D(
        lambda position, time: Vec3(math.cos(time), math.sin(time), position.x * 0.1),
        name="rotating-field",
    )
    grid = RegularGrid3D(
        AxisSample(-1.0, 1.0, 3),
        AxisSample(0.0, 0.0, 1),
        AxisSample(0.0, 0.0, 1),
    )
    animation = TimeVectorFieldAnimation3D(
        field=field,
        grid=grid,
        start_time=0.0,
        end_time=math.pi / 2.0,
        temporal_samples=3,
        name="rotating-field-view",
    )
    scene = registry.compile_scene(animation)

    assert len(scene.primitives) == 1
    glyphs = scene.primitives[0]
    assert isinstance(glyphs, VectorGlyphSet)
    assert glyphs.instance_count == 3
    assert scene.timeline.tracks[0].property_path == "vectors"

    end = scene.sample(scene.timeline.duration).get("rotating-field-view")
    assert isinstance(end, VectorGlyphSet)
    assert end.vectors[0].x == pytest.approx(0.0, abs=1e-10)
    assert end.vectors[0].y == pytest.approx(1.0)
