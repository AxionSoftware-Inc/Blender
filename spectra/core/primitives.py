from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Literal

from .transforms import Transform3D
from .types import Color, Vec3


PrimitiveKind = Literal[
    "point",
    "point_cloud",
    "polyline",
    "surface",
    "region",
    "vector_glyph",
    "vector_glyph_set",
    "text",
    "group",
    "camera",
]
CameraProjection = Literal["perspective", "orthographic"]


@dataclass(frozen=True, slots=True)
class Primitive:
    id: str
    kind: PrimitiveKind
    visible: bool = True
    opacity: float = 1.0
    transform: Transform3D = Transform3D()

    def __post_init__(self) -> None:
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError("Primitive opacity must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class Point(Primitive):
    position: Vec3 = Vec3(0.0, 0.0, 0.0)
    radius: float = 0.05
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    kind: PrimitiveKind = field(default="point", init=False)


@dataclass(frozen=True, slots=True)
class PointCloud(Primitive):
    """Batched points/particles intended for native/GPU instancing."""

    positions: tuple[Vec3, ...] = ()
    radius: float = 0.05
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    radii: tuple[float, ...] = ()
    colors: tuple[Color, ...] = ()
    kind: PrimitiveKind = field(default="point_cloud", init=False)

    def __post_init__(self) -> None:
        Primitive.__post_init__(self)
        if not self.positions:
            raise ValueError("PointCloud requires at least one position")
        if self.radius < 0.0:
            raise ValueError("PointCloud default radius cannot be negative")
        if self.radii:
            if len(self.radii) != len(self.positions):
                raise ValueError("PointCloud radii must match position count")
            if any(radius < 0.0 for radius in self.radii):
                raise ValueError("PointCloud radii cannot be negative")
        if self.colors and len(self.colors) != len(self.positions):
            raise ValueError("PointCloud colors must match position count")

    @property
    def instance_count(self) -> int:
        return len(self.positions)


@dataclass(frozen=True, slots=True)
class Polyline(Primitive):
    points: tuple[Vec3, ...] = ()
    width: float = 0.02
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    closed: bool = False
    trim_start: float = 0.0
    trim_end: float = 1.0
    kind: PrimitiveKind = field(default="polyline", init=False)

    def __post_init__(self) -> None:
        Primitive.__post_init__(self)
        if len(self.points) < 2:
            raise ValueError("Polyline requires at least two points")
        if not 0.0 <= self.trim_start <= 1.0 or not 0.0 <= self.trim_end <= 1.0:
            raise ValueError("Polyline trim values must be within [0, 1]")
        if self.trim_start > self.trim_end:
            raise ValueError("Polyline trim_start cannot exceed trim_end")


@dataclass(frozen=True, slots=True)
class Surface(Primitive):
    """Renderer-independent indexed triangle surface."""

    vertices: tuple[Vec3, ...] = ()
    triangles: tuple[tuple[int, int, int], ...] = ()
    color: Color = Color(0.8, 0.85, 1.0, 1.0)
    kind: PrimitiveKind = field(default="surface", init=False)

    def __post_init__(self) -> None:
        Primitive.__post_init__(self)
        if len(self.vertices) < 3:
            raise ValueError("Surface requires at least three vertices")
        if not self.triangles:
            raise ValueError("Surface requires at least one triangle")
        vertex_count = len(self.vertices)
        for triangle in self.triangles:
            if len(triangle) != 3:
                raise ValueError("Surface triangle must contain exactly three indices")
            if any(index < 0 or index >= vertex_count for index in triangle):
                raise ValueError("Surface triangle index is out of range")


@dataclass(frozen=True, slots=True)
class Region(Primitive):
    boundary: tuple[Vec3, ...] = ()
    color: Color = Color(1.0, 1.0, 1.0, 0.25)
    kind: PrimitiveKind = field(default="region", init=False)

    def __post_init__(self) -> None:
        Primitive.__post_init__(self)
        if len(self.boundary) < 3:
            raise ValueError("Region requires at least three boundary points")


@dataclass(frozen=True, slots=True)
class VectorGlyph(Primitive):
    """Single vector arrow primitive.

    Kept for small scenes and direct annotations. Dense fields should prefer
    VectorGlyphSet so backends can use GPU/native instancing efficiently.
    """

    origin: Vec3 = Vec3(0.0, 0.0, 0.0)
    vector: Vec3 = Vec3(1.0, 0.0, 0.0)
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    kind: PrimitiveKind = field(default="vector_glyph", init=False)


@dataclass(frozen=True, slots=True)
class VectorGlyphSet(Primitive):
    """Batched vector arrows intended for native/GPU instancing."""

    origins: tuple[Vec3, ...] = ()
    vectors: tuple[Vec3, ...] = ()
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    colors: tuple[Color, ...] = ()
    kind: PrimitiveKind = field(default="vector_glyph_set", init=False)

    def __post_init__(self) -> None:
        Primitive.__post_init__(self)
        if not self.origins:
            raise ValueError("VectorGlyphSet requires at least one instance")
        if len(self.origins) != len(self.vectors):
            raise ValueError("VectorGlyphSet origins and vectors must have equal lengths")
        if self.colors and len(self.colors) != len(self.origins):
            raise ValueError("VectorGlyphSet per-instance colors must match instance count")

    @property
    def instance_count(self) -> int:
        return len(self.origins)


@dataclass(frozen=True, slots=True)
class TextLabel(Primitive):
    text: str = ""
    position: Vec3 = Vec3(0.0, 0.0, 0.0)
    size: float = 1.0
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    kind: PrimitiveKind = field(default="text", init=False)


@dataclass(frozen=True, slots=True)
class Group(Primitive):
    children: tuple[str, ...] = ()
    kind: PrimitiveKind = field(default="group", init=False)


@dataclass(frozen=True, slots=True)
class Camera(Primitive):
    """Renderer-independent camera node.

    Convention: camera local -Z is forward and local +Y is up. Backends map this
    to their native camera convention.
    """

    projection: CameraProjection = "perspective"
    fov_y_radians: float = math.radians(50.0)
    orthographic_scale: float = 10.0
    near_clip: float = 0.01
    far_clip: float = 10000.0
    kind: PrimitiveKind = field(default="camera", init=False)

    def __post_init__(self) -> None:
        Primitive.__post_init__(self)
        if self.projection not in ("perspective", "orthographic"):
            raise ValueError(f"unknown camera projection: {self.projection}")
        if not 0.0 < self.fov_y_radians < math.pi:
            raise ValueError("camera fov_y_radians must lie within (0, pi)")
        if self.orthographic_scale <= 0.0:
            raise ValueError("camera orthographic_scale must be positive")
        if self.near_clip <= 0.0 or self.far_clip <= self.near_clip:
            raise ValueError("camera clipping range is invalid")
