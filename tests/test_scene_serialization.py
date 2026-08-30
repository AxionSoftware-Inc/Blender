from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.coordinates import CoordinateFrame3D
from spectra.core.primitives import Camera, Group, Point, Polyline, Surface, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.serialization import scene_from_json, scene_to_json
from spectra.core.transforms import Quaternion, Transform3D
from spectra.core.types import Color, Vec3


def test_scene_round_trips_through_versioned_json() -> None:
    camera = Camera(
        id="camera.main",
        transform=Transform3D.look_at(
            Vec3(5.0, -5.0, 4.0),
            Vec3(0.0, 0.0, 0.0),
            up=Vec3(0.0, 0.0, 1.0),
        ),
        fov_y_radians=0.9,
    )
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
            VectorGlyphSet(
                id="field",
                origins=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
                vectors=(Vec3(0.0, 1.0, 0.0), Vec3(0.0, 2.0, 0.0)),
                color=Color(0.2, 0.6, 1.0, 1.0),
                colors=(Color(1.0, 0.0, 0.0, 1.0), Color(0.0, 1.0, 0.0, 1.0)),
            ),
            Group(id="all", children=("probe", "curve", "triangle", "field")),
            camera,
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
        frame=CoordinateFrame3D(
            origin=Vec3(10.0, 0.0, 0.0),
            basis_x=Vec3(0.0, 1.0, 0.0),
            basis_y=Vec3(1.0, 0.0, 0.0),
            basis_z=Vec3(0.0, 0.0, -1.0),
        ),
        active_camera_id="camera.main",
    )

    payload = scene_to_json(scene)
    restored = scene_from_json(payload)

    assert restored == scene
    assert restored.active_camera() == camera
    assert '"schema": "spectra.scene"' in payload
    assert '"version": 4' in payload
    assert '"interpolation": "smooth"' in payload
    assert '"active_camera_id": "camera.main"' in payload
    assert '"kind": "vector_glyph_set"' in payload


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
    assert point.material_id is None
    assert scene.active_camera() is None
    assert scene.materials == ()


def test_scene_v2_remains_readable() -> None:
    payload = """
    {
      "schema": "spectra.scene",
      "version": 2,
      "frame": {
        "origin": [0, 0, 0],
        "basis_x": [1, 0, 0],
        "basis_y": [0, 1, 0],
        "basis_z": [0, 0, 1]
      },
      "active_camera_id": null,
      "primitives": [
        {
          "id": "curve",
          "kind": "polyline",
          "visible": true,
          "opacity": 1,
          "transform": {
            "translation": [0, 0, 0],
            "rotation": [1, 0, 0, 0],
            "scale": [1, 1, 1]
          },
          "points": [[0, 0, 0], [1, 1, 0]],
          "width": 0.02,
          "color": [1, 1, 1, 1],
          "closed": false,
          "trim_start": 0,
          "trim_end": 1
        }
      ],
      "timeline": {"duration": 0, "tracks": []}
    }
    """
    scene = scene_from_json(payload)
    assert scene.get("curve").kind == "polyline"


def test_scene_v3_remains_readable_without_material_resources() -> None:
    payload = """
    {
      "schema": "spectra.scene",
      "version": 3,
      "frame": {
        "origin": [0, 0, 0],
        "basis_x": [1, 0, 0],
        "basis_y": [0, 1, 0],
        "basis_z": [0, 0, 1]
      },
      "active_camera_id": null,
      "primitives": [
        {
          "id": "samples",
          "kind": "point_cloud",
          "visible": true,
          "opacity": 1,
          "transform": {
            "translation": [0, 0, 0],
            "rotation": [1, 0, 0, 0],
            "scale": [1, 1, 1]
          },
          "positions": [[0, 0, 0], [1, 0, 0]],
          "radius": 0.05,
          "color": [1, 1, 1, 1],
          "radii": [],
          "colors": []
        }
      ],
      "timeline": {"duration": 0, "tracks": []}
    }
    """
    scene = scene_from_json(payload)
    assert scene.get("samples").kind == "point_cloud"
    assert scene.materials == ()
