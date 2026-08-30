from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .types import Color, Vec3


PrimitiveKind = Literal["point", "polyline", "surface", "region", "vector_glyph", "text", "group"]


@dataclass(frozen=True, slots=True)
class Primitive:
    id: str
    kind: PrimitiveKind
    visible: bool = True


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
    kind: PrimitiveKind = field(default="polyline", init=False)

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("Polyline requires at least two points")


@dataclass(frozen=True, slots=True)
class Region(Primitive):
    boundary: tuple[Vec3, ...] = ()
    color: Color = Color(1.0, 1.0, 1.0, 0.25)
    kind: PrimitiveKind = field(default="region", init=False)

    def __post_init__(self) -> None:
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
