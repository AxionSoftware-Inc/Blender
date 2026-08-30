import pytest

from spectra.core.animation import Timeline, draw_track
from spectra.core.composition import compose_namespaced_scenes, compose_scenes, namespace_scene
from spectra.core.coordinates import CoordinateFrame3D
from spectra.core.materials import Material
from spectra.core.primitives import Camera, Group, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3


def _curve_scene() -> Scene:
    return Scene(
        primitives=(
            Polyline(
                id="curve",
                material_id="main",
                points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 1.0, 0.0)),
            ),
            Group(id="group", children=("curve",)),
        ),
        timeline=Timeline(
            duration=1.0,
            tracks=(draw_track("curve", start_time=0.0, end_time=1.0),),
        ),
        materials=(Material(id="main", base_color=Color(0.2, 0.6, 1.0, 1.0)),),
    )


def test_namespace_scene_rewrites_all_internal_references() -> None:
    scene = namespace_scene(_curve_scene(), "math")

    assert tuple(primitive.id for primitive in scene.primitives) == (
        "math/curve",
        "math/group",
    )
    curve = scene.get("math/curve")
    group = scene.get("math/group")
    assert curve.material_id == "math/main"
    assert isinstance(group, Group)
    assert group.children == ("math/curve",)
    assert scene.materials[0].id == "math/main"
    assert scene.timeline.tracks[0].target_id == "math/curve"


def test_namespaced_scenes_with_same_local_ids_can_be_composed() -> None:
    combined = compose_namespaced_scenes(
        (
            ("electric", _curve_scene()),
            ("magnetic", _curve_scene()),
        )
    )

    assert len(combined.primitives) == 4
    assert combined.get("electric/curve").id == "electric/curve"
    assert combined.get("magnetic/curve").id == "magnetic/curve"
    assert len(combined.timeline.tracks) == 2
    assert {track.target_id for track in combined.timeline.tracks} == {
        "electric/curve",
        "magnetic/curve",
    }


def test_namespace_preserves_and_rewrites_active_camera() -> None:
    scene = Scene(
        primitives=(Camera(id="camera"),),
        active_camera_id="camera",
    )
    namespaced = namespace_scene(scene, "lesson")

    assert namespaced.active_camera_id == "lesson/camera"
    assert namespaced.active_camera() is not None


def test_composition_requires_explicit_coordinate_frame_mapping() -> None:
    first = Scene()
    second = Scene(
        frame=CoordinateFrame3D(origin=Vec3(10.0, 0.0, 0.0)),
    )

    with pytest.raises(ValueError, match="CoordinateFrame3D"):
        compose_scenes(first, second)
