from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from spectra.core.scene import Scene

from .base import Backend, validate_backend_compatibility


HandleT = TypeVar("HandleT")


@dataclass
class BackendSession(Generic[HandleT]):
    """Drive any backend from the engine-owned timeline.

    The backend only receives static Scene snapshots. Seeking or playback does
    not delegate scientific timing semantics to Blender/WebGPU/etc.
    """

    backend: Backend[HandleT]
    source_scene: Scene
    handle: HandleT
    time: float = 0.0
    closed: bool = False

    @classmethod
    def open(cls, backend: Backend[HandleT], scene: Scene) -> "BackendSession[HandleT]":
        initial = scene.sample(0.0)
        validate_backend_compatibility(initial, backend.capabilities)
        handle = backend.create(initial)
        return cls(backend=backend, source_scene=scene, handle=handle)

    def seek(self, time: float) -> Scene:
        if self.closed:
            raise RuntimeError("backend session is closed")
        sampled = self.source_scene.sample(time)
        validate_backend_compatibility(sampled, self.backend.capabilities)
        self.backend.apply(self.handle, sampled)
        self.time = min(max(float(time), 0.0), self.source_scene.timeline.duration)
        return sampled

    def close(self) -> None:
        if self.closed:
            return
        self.backend.destroy(self.handle)
        self.closed = True
