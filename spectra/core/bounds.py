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
        # Degenerate content still receives a small non-zero extent so camera
        # fitting and clipping remain well-defined.
        epsilon = max(self.diagonal * 1e-6, 1e-6)
        half = Vec3(
            max(abs(half.x), epsilon),
            max(abs(half.y), epsilon),
            max(abs(half.z), epsilon),
        )
        return Bounds3D(center - half, center + half)


def _scene_point(scene: Scene, primitive: Primitive, point: Vec3) -> Vec3:
    local = primitive.transform.apply_point(point)
    return scene.frame.point_to_parent(local)


def primitive_bounds(scene: Scene, primitive: Primitive) -> Bounds3D | None:
    """Return conservative world/parent-space bounds for one visible primitive.

    Groups currently organize references but do not contribute geometry. Camera
    nodes are presentation controls and are excluded from content bounds.
    """
    if not primitive.visible or primitive.opacity <= 0.0:
        return None
    if isinstance(primitive, (Camera, Group)):
        return None

    if isinstance(primitive, Point):
        center = _scene_point(scene, primitive, primitive.position)
        radius = abs(primitive.radius) * primitive.transform.max_abs_scale
        # CoordinateFrame3D may itself contain scale/shear-like basis lengths;
        # transform local radius along each parent basis for a conservative AABB.
        extent_x = max(
            abs(scene.frame.basis_x.x),
            abs(scene.frame.basis_y.x),
            abs(scene.frame.basis_z.x),
        ) * radius
        extent_y = max(
            abs(scene.frame.basis_x.y),
            abs(scene.frame.basis_y.y),
            abs(scene.frame.basis_z.y),
        ) * radius
        extent_z = max(
            abs(scene.frame.basis_x.z),
            abs(scene.frame.basis_y.z),
            abs(scene.frame.basis_z.z),
        ) * radius
        extent = Vec3(extent_x, extent_y, extent_z)
        return Bounds3D(center - extent, center + extent)

    if isinstance(primitive, Polyline):
        return Bounds3D.from_points(
            _scene_point(scene, primitive, point) for point in primitive.points
        )

    if isinstance(primitive, Surface):
        return Bounds3D.from_points(
            _scene_point(scene, primitive, vertex) for vertex in primitive.vertices
        )

    if isinstance(primitive, Region):
        return Bounds3D.from_points(
            _scene_point(scene, primitive, point) for point in primitive.boundary
        )

    if isinstance(primitive, VectorGlyph):
        start = _scene_point(scene, primitive, primitive.origin)
        end = _scene_point(scene, primitive, primitive.origin + primitive.vector)
        return Bounds3D.from_points((start, end))

    if isinstance(primitive, TextLabel):
        # Font metrics are renderer-dependent. Treat the anchor as content for
        # framing; backends may add their own screen-space padding.
        anchor = _scene_point(scene, primitive, primitive.position)
        return Bounds3D(anchor, anchor)

    raise SceneBoundsError(f"unsupported primitive for bounds: {type(primitive).__qualname__}")


def scene_bounds(scene: Scene, *, padding: float = 1.0) -> Bounds3D:
    """Compute renderer-independent bounds of visible scientific content."""
    combined: Bounds3D | None = None
    for primitive in scene.primitives:
        bounds = primitive_bounds(scene, primitive)
        if bounds is None:
            continue
        combined = bounds if combined is None else combined.include(bounds)

    if combined is None:
        raise SceneBoundsError("Scene contains no visible geometric content")
    return combined if padding == 1.0 else combined.padded(padding)
