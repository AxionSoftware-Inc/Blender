from spectra.compiler import sample_function
from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Point
from spectra.core.scene import Scene
from spectra.core.types import Vec3


def test_scene_rejects_duplicate_ids() -> None:
    point = Point(id="p", position=Vec3(0.0, 0.0, 0.0))
    try:
        Scene(primitives=(point, point))
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate primitive ids should fail")


def test_function_compiles_without_renderer() -> None:
    scene = sample_function(lambda x: x * x, x_min=-2.0, x_max=2.0, samples=5)
    curve = scene.get("function")
    assert curve.kind == "polyline"
    assert len(curve.points) == 5
    assert curve.points[0] == Vec3(-2.0, 4.0, 0.0)
    assert curve.points[-1] == Vec3(2.0, 4.0, 0.0)


def test_animation_time_is_engine_owned() -> None:
    track = Track(
        target_id="p",
        property_path="position",
        keyframes=(Keyframe(0.0, Vec3(0.0, 0.0, 0.0)), Keyframe(1.0, Vec3(1.0, 0.0, 0.0))),
    )
    timeline = Timeline(duration=1.0, tracks=(track,))
    scene = Scene(primitives=(Point(id="p"),), timeline=timeline)
    assert scene.timeline.duration == 1.0
    assert scene.timeline.tracks[0].keyframes[-1].time == 1.0
