from __future__ import annotations

from dataclasses import replace
import math

from .bounds import Bounds3D, scene_local_bounds
from .primitives import Camera
from .scene import Scene
from .transforms import Transform3D
from .types import Vec3


def fit_camera_to_bounds(
    bounds: Bounds3D,
    *,
    camera_id: str = "camera.auto",
    projection: str = "perspective",
    aspect_ratio: float = 16.0 / 9.0,
    fov_y_radians: float = math.radians(50.0),
    margin: float = 1.2,
    direction: Vec3 = Vec3(1.0, 0.75, 1.0),
    up: Vec3 = Vec3(0.0, 1.0, 0.0),
) -> Camera:
    """Create a renderer-independent camera that safely frames Bounds3D.

    A bounding sphere is used deliberately: it is conservative, stable across
    backend conventions, and avoids coupling the core to a renderer's exact
    frustum implementation.
    """
    if not camera_id:
        raise ValueError("camera_id cannot be empty")
    if projection not in ("perspective", "orthographic"):
        raise ValueError(f"unknown camera projection: {projection}")
    if not math.isfinite(aspect_ratio) or aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be finite and positive")
    if not 0.0 < fov_y_radians < math.pi:
        raise ValueError("fov_y_radians must lie within (0, pi)")
    if not math.isfinite(margin) or margin < 1.0:
        raise ValueError("camera framing margin must be finite and >= 1")

    direction = direction.normalized()
    center = bounds.center
    radius = max(bounds.bounding_sphere_radius, 1e-6)

    if projection == "perspective":
        half_y = fov_y_radians * 0.5
        half_x = math.atan(math.tan(half_y) * aspect_ratio)
        limiting_half_angle = min(half_x, half_y)
        distance = (radius * margin) / max(math.sin(limiting_half_angle), 1e-6)
        eye = center + direction * distance

        padded_radius = radius * margin
        near_clip = max(1e-4, distance - padded_radius * 1.25)
        far_clip = max(near_clip + 1.0, distance + padded_radius * 2.0)
        return Camera(
            id=camera_id,
            projection="perspective",
            fov_y_radians=fov_y_radians,
            near_clip=near_clip,
            far_clip=far_clip,
            transform=Transform3D.look_at(eye, center, up=up),
        )

    # Camera.orthographic_scale is defined as the visible vertical span. A
    # bounding sphere keeps the framing conservative for arbitrary view angles.
    vertical_span = 2.0 * radius * margin
    if aspect_ratio < 1.0:
        vertical_span /= aspect_ratio
    eye_distance = max(radius * margin * 2.0, 1.0)
    eye = center + direction * eye_distance
    return Camera(
        id=camera_id,
        projection="orthographic",
        orthographic_scale=max(vertical_span, 1e-6),
        near_clip=max(1e-4, eye_distance - radius * margin * 1.5),
        far_clip=max(2.0, eye_distance + radius * margin * 2.0),
        transform=Transform3D.look_at(eye, center, up=up),
    )


def fit_camera_to_scene(
    scene: Scene,
    *,
    time: float | None = None,
    padding: float = 1.0,
    **camera_options: object,
) -> Camera:
    """Fit a Camera to Scene-local scientific content.

    When ``time`` is supplied, an animated Scene is sampled first, allowing a
    caller to frame a particular scientific moment without renderer involvement.
    """
    target_scene = scene.sample(time) if time is not None else scene
    bounds = scene_local_bounds(target_scene, padding=padding)
    return fit_camera_to_bounds(bounds, **camera_options)


def with_fitted_camera(
    scene: Scene,
    *,
    time: float | None = None,
    padding: float = 1.0,
    **camera_options: object,
) -> Scene:
    """Return Scene with an auto-fitted active Camera, preserving all semantics."""
    camera = fit_camera_to_scene(scene, time=time, padding=padding, **camera_options)

    existing = None
    for primitive in scene.primitives:
        if primitive.id == camera.id:
            existing = primitive
            break
    if existing is not None and not isinstance(existing, Camera):
        raise ValueError(
            f"auto camera id '{camera.id}' conflicts with non-camera primitive"
        )

    primitives = tuple(
        camera if primitive.id == camera.id else primitive
        for primitive in scene.primitives
    )
    if existing is None:
        primitives = (*primitives, camera)

    return replace(scene, primitives=primitives, active_camera_id=camera.id)
