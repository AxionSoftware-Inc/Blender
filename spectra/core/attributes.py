from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from .types import Color, Vec2, Vec3
from .units import Unit

VisualAttributeAssociation = Literal["vertex", "instance", "primitive"]
VisualAttributeKind = Literal["scalar", "vec2", "vec3", "color"]


@dataclass(frozen=True, slots=True)
class VisualAttribute:
    name: str
    association: VisualAttributeAssociation
    kind: VisualAttributeKind
    values: tuple[float | Vec2 | Vec3 | Color, ...]
    quantity_id: str | None = None
    unit: Unit | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("visual attribute name cannot be empty")
        if self.association not in {"vertex", "instance", "primitive"}:
            raise ValueError(f"unknown visual attribute association: {self.association}")
        if self.kind not in {"scalar", "vec2", "vec3", "color"}:
            raise ValueError(f"unknown visual attribute kind: {self.kind}")
        if not self.values:
            raise ValueError("visual attribute values cannot be empty")
        expected = {"scalar": (int, float), "vec2": (Vec2,), "vec3": (Vec3,), "color": (Color,)}[self.kind]
        for value in self.values:
            if not isinstance(value, expected) or isinstance(value, bool):
                raise TypeError(f"attribute '{self.name}' contains a value incompatible with {self.kind}")
            if self.kind == "scalar" and not math.isfinite(float(value)):
                raise ValueError(f"attribute '{self.name}' contains a non-finite scalar")
        if self.kind == "color" and self.unit is not None:
            raise ValueError("color visual attributes cannot carry a unit")


@dataclass(frozen=True, slots=True)
class VisualAttributeSet:
    attributes: tuple[VisualAttribute, ...] = ()

    def __post_init__(self) -> None:
        names = [attribute.name for attribute in self.attributes]
        if len(names) != len(set(names)):
            raise ValueError("visual attribute names must be unique")

    def get(self, name: str) -> VisualAttribute:
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute
        raise KeyError(name)

    def __bool__(self) -> bool:
        return bool(self.attributes)


def validate_primitive_attributes(primitive: object) -> None:
    attributes = getattr(primitive, "attributes", VisualAttributeSet())
    expected = None
    if primitive.__class__.__name__ == "Surface":
        expected = {"vertex": len(primitive.vertices), "primitive": 1}
    elif primitive.__class__.__name__ == "PointCloud":
        expected = {"instance": len(primitive.positions), "primitive": 1}
    elif primitive.__class__.__name__ == "VectorGlyphSet":
        expected = {"instance": len(primitive.origins), "primitive": 1}
    elif primitive.__class__.__name__ == "Polyline":
        expected = {"vertex": len(primitive.points), "primitive": 1}
    for attribute in attributes.attributes:
        if expected is not None and attribute.association in expected and len(attribute.values) != expected[attribute.association]:
            raise ValueError(f"visual attribute '{attribute.name}' length does not match {attribute.association} count")


__all__ = ["VisualAttribute", "VisualAttributeSet", "validate_primitive_attributes"]
