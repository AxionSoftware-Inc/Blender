from __future__ import annotations

from dataclasses import dataclass

from spectra.core.scene import Scene

from .base import BackendCapabilities


@dataclass
class MemoryHandle:
    scene: Scene
    destroyed: bool = False


class MemoryBackend:
    """Reference backend used to prove the adapter contract without a renderer."""

    name = "memory"
    capabilities = BackendCapabilities.all_core_primitives()

    def create(self, scene: Scene) -> MemoryHandle:
        return MemoryHandle(scene=scene)

    def apply(self, handle: MemoryHandle, scene: Scene) -> None:
        if handle.destroyed:
            raise RuntimeError("memory backend handle is destroyed")
        handle.scene = scene

    def destroy(self, handle: MemoryHandle) -> None:
        handle.destroyed = True
