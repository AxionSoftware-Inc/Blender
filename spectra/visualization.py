from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from spectra.core.scene import Scene


SceneCompiler = Callable[[Any], Scene]


class VisualizationCompileError(LookupError):
    """Raised when no semantic-to-Scene compiler is registered for a value."""


@dataclass
class VisualizationRegistry:
    """Type-directed semantic -> Scene compiler registry.

    Domains register compilers for their public semantic types. Callers can then
    compile a semantic object without knowing which domain owns it or which
    concrete compiler function should be called.
    """

    _compilers: dict[type[Any], SceneCompiler] = field(default_factory=dict)

    def register(self, semantic_type: type[Any], compiler: SceneCompiler) -> None:
        if semantic_type in self._compilers:
            raise ValueError(
                f"visualization compiler already registered for: {semantic_type.__qualname__}"
            )
        self._compilers[semantic_type] = compiler

    def supports(self, value_or_type: Any) -> bool:
        semantic_type = value_or_type if isinstance(value_or_type, type) else type(value_or_type)
        return self._resolve_type(semantic_type) is not None

    def compile(self, value: Any) -> Scene:
        semantic_type = type(value)
        registered_type = self._resolve_type(semantic_type)
        if registered_type is None:
            raise VisualizationCompileError(
                f"no visualization compiler registered for: {semantic_type.__module__}.{semantic_type.__qualname__}"
            )
        return self._compilers[registered_type](value)

    def _resolve_type(self, semantic_type: type[Any]) -> type[Any] | None:
        # Respect Python's normal inheritance order so a specialized compiler can
        # override a compiler registered for a base semantic type.
        for candidate in semantic_type.__mro__:
            if candidate in self._compilers:
                return candidate
        return None
