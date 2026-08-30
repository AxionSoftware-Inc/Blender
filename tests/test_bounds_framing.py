import pytest

from spectra.core.bounds import scene_bounds, scene_local_bounds
from spectra.core.coordinates import CoordinateFrame3D
from spectra.core.framing import fit_camera_to_scene, with_fitted_camera
from spectra.core.primitives import Camera, Point, Polyline
from spectra.core.scene import Scene
from spectra.core.transforms import Transform3D
from spectra.core.types import Vec3


def test_scene_local_and_parent_bounds_are_distinct() -> None:
    scene = Scene(
        primitives=(
            Polyline(
                id="curve",
                points=(Vec3(-1.0, 0.0, 0.0), Vec3(2.0, 3.0, 0.0)),
                transform=Transform3D(translation=Vec3(1.0, 2.0, 0.0)),
            ),
        ),
        frame=CoordinateFrame3D(
            origin=Vec3(10.0, 20.0, 30.0),
            basis_x=Vec3(2.0, 0.0, 0.0),
            basis_y=Vec3(0.0, 3.0, 0.0),
            basis_z=Vec3(0.0, 0.0, 4.0),
        ),
    )

    local = scene_local_bounds(scene)
    assert local.minimum == Vec3(0.0, 2.0, 0.0)
    assert local.maximum == Vec3(3.0, 5.0, 0.0)

    parent = scene_bounds(scene)
    assert parent.minimum == Vec3(10.0, 26.0, 30.0)
    assert parent.maximum == Vec3(16.0, 35.0, 30.0)


def test_point_bounds_include_visual_transform_scale() -> None:
    scene = Scene(
        primitives=(
            Point(
                id="probe",
                position=Vec3(1.0, 0.0, 0.0),
                radius=0.5,
                transform=Transform3D(
                    translation=Vec3(2.0, 0.0, 0.0),
                    scale=Vec3(2.0, 1.0, 1.0),
                ),
            ),
        )
    )

    bounds = scene_local_bounds(scene)
    assert bounds.minimum == Vec3(3.0, -1.0, -1.0)
    assert bounds.maximum == Vec3(5.0, 1.0, 1.0)


def test_auto_camera_frames_scene_and_becomes_active() -> None:
    scene = Scene(
        primitives=(
            Polyline(
                id="trajectory",
                points=(
                    Vec3(-2.0, -1.0, 0.0),
                    Vec3(0.0, 3.0, 1.0),
                    Vec3(4.0, 1.0, -1.0),
                ),
            ),
        )
    )

    camera = fit_camera_to_scene(scene, aspect_ratio=16.0 / 9.0)
    assert isinstance(camera, Camera)
    assert camera.near_clip > 0.0
    assert camera.far_clip > camera.near_clip

    center = scene_local_bounds(scene).center
    expected_forward = (center - camera.transform.translation).normalized()
    actual_forward = camera.transform.rotation.rotate(Vec3(0.0, 0.0, -1.0)).normalized()
    assert actual_forward.dot(expected_forward) == pytest.approx(1.0, abs=1e-7)

    framed = with_fitted_camera(scene, camera_id="camera.main")
    assert framed.active_camera_id == "camera.main"
    assert isinstance(framed.active_camera(), Camera)
    assert len(framed.primitives) == 2
