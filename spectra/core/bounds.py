from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .primitives import Camera, Group, Point, Polyline, Primitive, Region, Surface, TextLabel, VectorGlyph
from .scene import Scene
from .types import Vec3


class SceneBoundsError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Bounds3D:
    minimum: Vec3
    maximum: Vec3

    def __post_init__(self) -> None:
        if (
            self.minimum.x > self.maximum.x
            or self.minimum.y > self.maximum.y
            or self.minimum.z > self.maximum.z
        ):
            raise ValueError("bounds minimum cannot exceed maximum")

    @classmethod
    def from_points(cls, points: Iterable[Vec3]) -> "Bounds3D":
        iterator = iter(points)
        try:
            first = next(iterator)
        except StopIteration as exc:
            raise ValueError("cannot create Bounds3D from no points") from exc

        min_x = max_x = first.x
        min_y = max_y = first.y
        min_z = max_z = first.z
        for point in iterator:
            min_x = min(min_x, point.x)
            min_y = min(min_y, point.y)
            min_z = min(min_z, point.z)
            max_x = max(max_x, point.x)
            max_y = max(max_y, point.y)
            max_z = max(max_z, point.z)
        return cls(Vec3(min_x, min_y, min_z), Vec3(max_x, max_y, max_z))

    @property
    def center(self) -> Vec3:
        return (self.minimum + self.maximum) * 0.5

    @property
    def size(self) -> Vec3:
        return self.maximum - self.minimum

    @property
    def diagonal(self) -> float:
        return self.size.magnitude

    @property
    def bounding_sphere_radius(self) -> float:
        return self.diagonal * 0.5

    @property
    def corners(self) -> tuple[Vec3, ...]:
        low = self.minimum
        high = self.maximum
        return tuple(
            Vec3(x, y, z)
            for x in (low.x, high.x)
            for y in (low.y, high.y)
            for z in (low.z, high.z)
        )

    def include(self, other: "Bounds3D") -> "Bounds3D":
        return Bounds3D(
            minimum=Vec3(
                min(self.minimum.x, other.minimum.x),
                min(self.minimum.y, other.minimum.y),
                min(self.minimum.z, other.minimum.z),
            ),
            maximum=Vec3(
                max(self.maximum.x, other.maximum.x),
                max(self.maximum.y, other.maximum.y),
                max(self.maximum.z, other.maximum.z),
            ),
        )

    def padded(self, factor: float) -> "Bounds3D":
        if factor < 1.0 or not math.isfinite(factor):
            raise ValueError("bounds padding factor must be finite and >= 1")
        half = self.size * (0.5 * factor)
        center = self.center
        epsilon = max(self.diagonal * 1e-6, 1e-6)
        half = Vec3(
            max(abs(half.x), epsilon),
            max(abs(half.y), epsilon),
            max(abs(half.z), epsilon),
        )
        return Bounds3D(center - half, center + half)


def _local_point(primitive: Primitive, point: Vec3) -> Vec3:
    return primitive.transform.apply_point(point)


def primitive_local_bounds(primitive: Primitive) -> Bounds3D | None:
    """Return Scene-local bounds for one visible scientific primitive.

    Primitive transforms are applied, but the Scene coordinate frame is not.
    Cameras and Groups do not contribute geometry. Polyline trim is intentionally
    ignored so framing remains conservative during reveal animations.
    """
    if not primitive.visible or primitive.opacity <= 0.0:
        return None
    if isinstance(primitive, (Camera, Group)):
        return None

    if isinstance(primitive, Point):
        center = _local_point(primitive, primitive.position)
        radius = abs(primitive.radius) * primitive.transform.max_abs_scale
        extent = Vec3(radius, radius, radius)
        return Bounds3D(center - extent, center + extent)

    if isinstance(primitive, Polyline):
        return Bounds3D.from_points(_local_point(primitive, point) for point in primitive.points)

    if isinstance(primitive, Surface):
        return Bounds3D.from_points(_local_point(primitive, vertex) for vertex in primitive.vertices)

    if isinstance(primitive, Region):
        return Bounds3D.from_points(_local_point(primitive, point) for point in primitive.boundary)

    if isinstance(primitive, VectorGlyph):
        start = _local_point(primitive, primitive.origin)
        end = _local_point(primitive, primitive.origin + primitive.vector)
        return Bounds3D.from_points((start, end))

    if isinstance(primitive, TextLabel):
        # Exact text bounds require renderer/font metrics. The anchor is still
        # useful for scientific framing; backends may add screen-space padding.
        anchor = _local_point(primitive, primitive.position)
        return Bounds3D(anchor, anchor)

    raise SceneBoundsError(f"unsupported primitive for bounds: {type(primitive).__qualname__}")


def scene_local_bounds(scene: Scene, *, padding: float = 1.0) -> Bounds3D:
    """Bounds in the Scene's scientific coordinate space.

    This is the correct space for renderer-independent camera fitting because
    Camera transforms live in the same Scene-local coordinate system.
    """
    combined: Bounds3D | None = None
    for primitive in scene.primitives:
        bounds = primitive_local_bounds(primitive)
        if bounds is None:
            continue
        combined = bounds if combined is None else combined.include(bounds)

    if combined is None:
        raise SceneBoundsError("Scene contains no visible geometric content")
    return combined if padding == 1.0 else combined.padded(padding)


def _map_bounds_to_parent(scene: Scene, bounds: Bounds3D) -> Bounds3D:
    return Bounds3D.from_points(scene.frame.point_to_parent(corner) for corner in bounds.corners)


def primitive_bounds(scene: Scene, primitive: Primitive) -> Bounds3D | None:
    """Return conservative parent/world-mapped bounds for one primitive.

    This preserves the original public behavior of primitive_bounds while the
    new primitive_local_bounds API makes coordinate-space ownership explicit.
    """
    local = primitive_local_bounds(primitive)
    if local is None:
        return None
    return _map_bounds_to_parent(scene, local)


def scene_bounds(scene: Scene, *, padding: float = 1.0) -> Bounds3D:
    """Compute parent/world-mapped bounds of visible scientific content."""
    local = scene_local_bounds(scene, padding=padding)
    return _map_bounds_to_parent(scene, local)
