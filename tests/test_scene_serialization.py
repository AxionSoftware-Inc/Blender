from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Group, Point, Polyline, Surface
from spectra.core.scene import Scene
from spectra.core.serialization import scene_from_json, scene_to_json
from spectra.core.transforms import Quaternion, Transform3D
from spectra.core.types import Color, Vec3


def test_scene_round_trips_through_versioned_json() -> None:
    scene = Scene(
        primitives=(
            Point(
                id="probe",
                position=Vec3(1.0, 2.0, 3.0),
                radius=0.2,
                opacity=0.75,
                transform=Transform3D(
                    translation=Vec3(2.0, 0.0, 0.0),
                    rotation=Quaternion.from_axis_angle(Vec3(0.0, 0.0, 1.0), 0.5),
                ),
                color=Color(1.0, 0.5, 0.25, 1.0),
            ),
            Polyline(
                id="curve",
                points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 1.0, 0.0)),
                trim_start=0.1,
                trim_end=0.8,
            ),
            Surface(
                id="triangle",
                vertices=(
                    Vec3(0.0, 0.0, 0.0),
                    Vec3(1.0, 0.0, 0.0),
                    Vec3(0.0, 1.0, 0.0),
                ),
                triangles=((0, 1, 2),),
            ),
            Group(id="all", children=("probe", "curve", "triangle")),
        ),
        timeline=Timeline(
            duration=2.0,
            tracks=(
                Track(
                    target_id="probe",
                    property_path="position",
                    keyframes=(
                        Keyframe(0.0, Vec3(1.0, 2.0, 3.0), "smooth"),
                        Keyframe(2.0, Vec3(4.0, 5.0, 6.0)),
                    ),
                ),
            ),
        ),
    )

    payload = scene_to_json(scene)
    restored = scene_from_json(payload)

    assert restored == scene
    assert '"schema": "spectra.scene"' in payload
    assert '"version": 2' in payload
    assert '"interpolation": "smooth"' in payload


def test_scene_v1_defaults_new_visual_fields() -> None:
    payload = """
    {
      "schema": "spectra.scene",
      "version": 1,
      "primitives": [
        {
          "id": "p",
          "kind": "point",
          "visible": true,
          "position": [1, 2, 3],
          "radius": 0.1,
          "color": [1, 1, 1, 1]
        }
      ],
      "timeline": {"duration": 0, "tracks": []}
    }
    """

    scene = scene_from_json(payload)
    point = scene.get("p")
    assert point.opacity == 1.0
    assert point.transform == Transform3D()
