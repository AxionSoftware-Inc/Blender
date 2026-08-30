from __future__ import annotations

from typing import Protocol

from spectra.core.scene import Scene


class Backend(Protocol):
    """Renderer boundary. Implementations may depend on Blender/WebGPU/etc."""

    def render(self, scene: Scene) -> object:
        ...
