from __future__ import annotations

from spectra.color_scales import map_scalar_values, resolve_scalar_range
from spectra.core.animation import Timeline, draw_track
from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.primitives import PointCloud, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Vec3
from spectra.presentation import compose_presentation
from spectra.presentation_models import (
    ColorPalette,
    ColorRangeMode,
    ColorScalePolicy,
    PresentationContext,
)


def test_fixed_and_symmetric_scalar_ranges() -> None:
    fixed = ColorScalePolicy(
        range_mode=ColorRangeMode.FIXED,
        minimum=-2.0,
        maximum=8.0,
    )
    assert resolve_scalar_range((-100.0, 100.0), fixed) == (-2.0, 8.0)

    symmetric = ColorScalePolicy(
        palette=ColorPalette.COOLWARM,
        range_mode=ColorRangeMode.SYMMETRIC,
        center=1.0,
    )
    assert resolve_scalar_range((-2.0, 4.0), symmetric) == (-2.0, 4.0)


def test_scalar_mapping_is_deterministic_and_bounded() -> None:
    policy = ColorScalePolicy(palette=ColorPalette.VIRIDIS)
    first = map_scalar_values((0.0, 0.5, 1.0), policy)
    second = map_scalar_values((0.0, 0.5, 1.0), policy)
    assert first == second
    assert first[0] != first[-1]
    for color in first:
        assert 0.0 <= color.r <= 1.0
        assert 0.0 <= color.g <= 1.0
        assert 0.0 <= color.b <= 1.0
        assert 0.0 <= color.a <= 1.0


def test_compose_presentation_colorizes_instance_scalar_attribute() -> None:
    temperature = VisualAttribute(
        name="temperature",
        association="instance",
        kind="scalar",
        values=(280.0, 300.0, 320.0),
        quantity_id="temperature",
    )
    cloud = PointCloud(
        id="particles",
        positions=(Vec3(-1.0, 0.0, 0.0), Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
        attributes=VisualAttributeSet((temperature,)),
    )
    source = Scene(primitives=(cloud,))

    composed = compose_presentation(
        source,
        "presentation",
        context=PresentationContext(quantity_role="temperature"),
    )

    rendered = composed.get("particles")
    display = rendered.attributes.get("display_color")
    assert display.kind == "color"
    assert display.association == "instance"
    assert display.quantity_id == "temperature"
    assert len(display.values) == 3
    assert rendered.colors == display.values
    assert source.get("particles").colors == ()
    assert any(
        track.target_id == "particles" and track.property_path == "opacity"
        for track in composed.timeline.tracks
    )


def test_presentation_reveal_does_not_override_scientific_track() -> None:
    line = Polyline(
        id="trajectory",
        points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(2.0, 0.0, 0.0)),
    )
    scientific = Timeline(
        duration=1.0,
        tracks=(draw_track("trajectory", start_time=0.0, end_time=1.0),),
    )
    scene = Scene(primitives=(line,), timeline=scientific)

    composed = compose_presentation(scene, "presentation")
    matching = [
        track
        for track in composed.timeline.tracks
        if track.target_id == "trajectory" and track.property_path == "trim_end"
    ]
    assert len(matching) == 1
    assert matching[0] == scientific.tracks[0]


def test_explicit_scalar_attribute_can_drive_color_without_quantity_role() -> None:
    scalar = VisualAttribute(
        name="stress",
        association="instance",
        kind="scalar",
        values=(-1.0, 0.0, 2.0),
    )
    cloud = PointCloud(
        id="stress_points",
        positions=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(2.0, 0.0, 0.0)),
        attributes=VisualAttributeSet((scalar,)),
    )
    intent_policy = ColorScalePolicy(
        palette=ColorPalette.COOLWARM,
        range_mode=ColorRangeMode.SYMMETRIC,
        scalar_attribute_name="stress",
    )

    from spectra.presentation_models import PresentationIntent

    composed = compose_presentation(
        Scene(primitives=(cloud,)),
        PresentationIntent(preset="analysis", color_scale=intent_policy),
    )
    rendered = composed.get("stress_points")
    assert rendered.attributes.get("display_color").kind == "color"
    assert len(rendered.colors) == 3
