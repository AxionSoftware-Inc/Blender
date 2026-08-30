from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .types import Color


ShadingModel = Literal["unlit", "lit"]


@dataclass(frozen=True, slots=True)
class Material:
    """Renderer-independent visual material resource.

    Scientific compilers may usually rely on primitive colors. Materials are for
    reusable presentation intent that should survive backend changes. Backends
    map this compact contract to Blender nodes, realtime shaders, or another
    native material system.
    """

    id: str
    base_color: Color = Color(1.0, 1.0, 1.0, 1.0)
    shading: ShadingModel = "unlit"
    metallic: float = 0.0
    roughness: float = 0.5
    emission_color: Color = Color(0.0, 0.0, 0.0, 1.0)
    emission_strength: float = 0.0
    double_sided: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Material id cannot be empty")
        if self.shading not in ("unlit", "lit"):
            raise ValueError(f"unknown material shading model: {self.shading}")
        if not 0.0 <= self.metallic <= 1.0:
            raise ValueError("Material metallic must be within [0, 1]")
        if not 0.0 <= self.roughness <= 1.0:
            raise ValueError("Material roughness must be within [0, 1]")
        if self.emission_strength < 0.0:
            raise ValueError("Material emission_strength cannot be negative")
