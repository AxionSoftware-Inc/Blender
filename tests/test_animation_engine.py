from __future__ import annotations

import math

import pytest

from spectra.core.animation import Keyframe, Timeline, Track, draw_track, fade_track, move_track
from spectra.core.primitives import Group, Point, Polyline
from spectra.core.scene import Scene
from spectra.core.transforms import Quaternion
from spectra.core.types import Vec3


def test_scene_samples_renderer_independent_animation() -> None:
    curve = Polyline(
        id="curve",
        points=(Vec3(0.0, 0.0, 0.0), Vec3(2.0, 1.0, 0.0)),
    )
    marker = Point(id="marker", position=Vec3(0.0, 0.0, 0.0))
    scene = Scene(
        primitives=(curve, marker),
        timeline=Timeline(
            duration=2.0,
            tracks=(
                draw_track("curve", start_time=0.0, end_time=2.0),
                fade_track("marker", start_time=0.0, end_time=2.0),
                move_track(
                    "marker",
                    Vec3(0.0, 0.0, 0.0),
                    Vec3(10.0, 0.0, 0.0),
                    start_time=0.0,
                    end_time=2.0,
                ),
            ),
        ),
    )

    sampled = scene.sample(1.0)
    sampled_curve = sampled.get("curve")
    sampled_marker = sampled.get("marker")

    assert isinstance(sampled_curve, Polyline)
    assert math.isclose(sampled_curve.trim_end, 0.5)
    assert math.isclose(sampled_marker.opacity, 0.5)
    assert sampled_marker.transform.translation == Vec3(5.0, 0.0, 0.0)
    assert sampled.timeline.tracks == ()


def test_quaternion_rotation_is_interpolated_by_engine() -> None:
    point = Point(id="point")
    half_turn = Quaternion.from_axis_angle(Vec3(0.0, 0.0, 1.0), math.pi)
    scene = Scene(
        primitives=(point,),
        timeline=Timeline(
            duration=2.0,
            tracks=(
                Track(
                    target_id="point",
                    property_path="transform.rotation",
                    keyframes=(
                        Keyframe(0.0, Quaternion.identity()),
                        Keyframe(2.0, half_turn),
                    ),
                ),
            ),
        ),
    )

    rotation = scene.sample(1.0).get("point").transform.rotation
    expected = math.sqrt(0.5)
    assert math.isclose(abs(rotation.w), expected, rel_tol=1e-6)
    assert math.isclose(abs(rotation.z), expected, rel_tol=1e-6)


def test_scene_rejects_unknown_animation_target() -> None:
    with pytest.raises(ValueError, match="unknown primitive"):
        Scene(
            primitives=(Point(id="point"),),
            timeline=Timeline(
                duration=1.0,
                tracks=(
                    Track(
                        target_id="missing",
                        property_path="opacity",
                        keyframes=(Keyframe(0.0, 0.0), Keyframe(1.0, 1.0)),
                    ),
                ),
            ),
        )


def test_boolean_animation_requires_step_interpolation() -> None:
    with pytest.raises(TypeError, match="step interpolation"):
        Scene(
            primitives=(Point(id="point"),),
            timeline=Timeline(
                duration=1.0,
                tracks=(
                    Track(
                        target_id="point",
                        property_path="visible",
                        keyframes=(Keyframe(0.0, False), Keyframe(1.0, True)),
                    ),
                ),
            ),
        )


def test_group_hierarchy_rejects_cycles() -> None:
    with pytest.raises(ValueError, match="cycle"):
        Scene(
            primitives=(
                Group(id="a", children=("b",)),
                Group(id="b", children=("a",)),
            )
        )
