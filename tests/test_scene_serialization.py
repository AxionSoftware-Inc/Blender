from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Group, Point, Surface
from spectra.core.scene import Scene
from spectra.core.serialization import scene_from_json, scene_to_json
from spectra.core.types import Color, Vec3


def test_scene_round_trips_through_versioned_json() -> None:
    scene = Scene(
        primitives=(
            Point(
                id="probe",
                position=Vec3(1.0, 2.0, 3.0),
                radius=0.2,
                color=Color(1.0, 0.5, 0.25, 1.0),
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
            Group(id="all", children=("probe", "triangle")),
        ),
        timeline=Timeline(
            duration=2.0,
            tracks=(
                Track(
                    target_id="probe",
                    property_path="position",
                    keyframes=(
                        Keyframe(0.0, Vec3(1.0, 2.0, 3.0)),
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
    assert '"version": 1' in payload
