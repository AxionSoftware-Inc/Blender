from __future__ import annotations

from dataclasses import dataclass

from .animation import Timeline
from .primitives import Primitive


@dataclass(frozen=True, slots=True)
class Scene:
    primitives: tuple[Primitive, ...] = ()
    timeline: Timeline = Timeline()

    def __post_init__(self) -> None:
        ids = [primitive.id for primitive in self.primitives]
        if len(ids) != len(set(ids)):
            raise ValueError("Primitive ids must be unique within a Scene")

    def get(self, primitive_id: str) -> Primitive:
        for primitive in self.primitives:
            if primitive.id == primitive_id:
                return primitive
        raise KeyError(primitive_id)
