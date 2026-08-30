from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .transforms import Transform3D
from .types import Color, Vec3


PrimitiveKind = Literal["point", "polyline", "surface", "region", "vector_glyph", "text", "group"]


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
    origin: Vec3 = Vec3(0.0, 0.0, 0.0)
    vector: Vec3 = Vec3(1.0, 0.0, 0.0)
    color: Color = Color(1.0, 1.0, 1.0, 1.0)
    kind: PrimitiveKind = field(default="vector_glyph", init=False)


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
