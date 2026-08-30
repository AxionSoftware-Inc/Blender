from __future__ import annotations

import math

import pytest

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Camera, Point
from spectra.core.scene import Scene
from spectra.core.transforms import Transform3D
from spectra.core.types import Vec3


def test_look_at_camera_uses_local_negative_z_as_forward() -> None:
    eye = Vec3(3.0, -4.0, 2.0)
    target = Vec3(0.0, 0.0, 0.0)
    transform = Transform3D.look_at(eye, target, up=Vec3(0.0, 0.0, 1.0))

    world_forward = transform.rotation.rotate(Vec3(0.0, 0.0, -1.0))
    expected = (target - eye).normalized()

    assert transform.translation == eye
    assert world_forward.x == pytest.approx(expected.x, abs=1e-7)
    assert world_forward.y == pytest.approx(expected.y, abs=1e-7)
    assert world_forward.z == pytest.approx(expected.z, abs=1e-7)


def test_active_camera_must_reference_camera_primitive() -> None:
    with pytest.raises(ValueError, match="Camera primitive"):
        Scene(primitives=(Point(id="not-camera"),), active_camera_id="not-camera")


def test_camera_transform_can_be_animated_by_engine() -> None:
    camera = Camera(
        id="camera",
        transform=Transform3D.look_at(
            Vec3(0.0, -10.0, 5.0),
            Vec3(0.0, 0.0, 0.0),
            up=Vec3(0.0, 0.0, 1.0),
        ),
    )
    scene = Scene(
        primitives=(camera,),
        active_camera_id="camera",
        timeline=Timeline(
            duration=2.0,
            tracks=(
                Track(
                    target_id="camera",
                    property_path="transform.translation",
                    keyframes=(
                        Keyframe(0.0, Vec3(0.0, -10.0, 5.0), "smooth"),
                        Keyframe(2.0, Vec3(0.0, -6.0, 3.0)),
                    ),
                ),
            ),
        ),
    )

    sampled = scene.sample(1.0)
    translation = sampled.active_camera().transform.translation
    assert math.isclose(translation.y, -8.0)
    assert math.isclose(translation.z, 4.0)
