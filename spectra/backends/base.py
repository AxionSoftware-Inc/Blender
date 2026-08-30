from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

from spectra.core.primitives import PrimitiveKind
from spectra.core.scene import Scene


HandleT = TypeVar("HandleT")


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """Renderer features exposed to the engine without importing renderer SDKs."""

    primitive_kinds: frozenset[PrimitiveKind]
    supports_group_hierarchy: bool = True

    @classmethod
    def all_core_primitives(cls) -> "BackendCapabilities":
        return cls(
            frozenset(
                {
                    "point",
                    "polyline",
                    "surface",
                    "region",
                    "vector_glyph",
                    "text",
                    "group",
                    "camera",
                }
            )
        )


class BackendCompatibilityError(RuntimeError):
    pass


@runtime_checkable
class Backend(Protocol, Generic[HandleT]):
    """Minimal renderer adapter contract.

    Backends consume renderer-neutral *static* Scene snapshots. Timeline
    evaluation stays inside Spectra. A Blender/WebGPU/Unreal adapter therefore
    never needs to understand calculus, probability, mechanics, or another
    scientific domain.
    """

    name: str
    capabilities: BackendCapabilities

    def create(self, scene: Scene) -> HandleT:
        """Create native renderer resources for a static Scene snapshot."""
        ...

    def apply(self, handle: HandleT, scene: Scene) -> None:
        """Update an existing native scene from another static snapshot."""
        ...

    def destroy(self, handle: HandleT) -> None:
        """Release native renderer resources owned by this backend handle."""
        ...


def validate_backend_compatibility(scene: Scene, capabilities: BackendCapabilities) -> None:
    unsupported = sorted(
        {primitive.kind for primitive in scene.primitives}
        - set(capabilities.primitive_kinds)
    )
    if unsupported:
        raise BackendCompatibilityError(
            "backend does not support primitive kinds: " + ", ".join(unsupported)
        )
    if not capabilities.supports_group_hierarchy and any(
        primitive.kind == "group" for primitive in scene.primitives
    ):
        raise BackendCompatibilityError("backend does not support Scene group hierarchy")
