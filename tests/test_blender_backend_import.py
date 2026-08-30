from __future__ import annotations

import pytest

from spectra.backends import BlenderBackend, BlenderUnavailableError
from spectra.core.scene import Scene


def test_blender_backend_constructs_without_importing_blender_runtime() -> None:
    backend = BlenderBackend()
    assert backend.name == "blender"
    assert "surface" in backend.capabilities.primitive_kinds
    assert "camera" in backend.capabilities.primitive_kinds
    assert "light" in backend.capabilities.primitive_kinds
    assert "point_cloud" in backend.capabilities.primitive_kinds
    assert "vector_glyph_set" in backend.capabilities.primitive_kinds


def test_blender_dependency_is_required_only_when_backend_executes(monkeypatch: pytest.MonkeyPatch) -> None:
    import spectra.backends.blender.backend as blender_module

    real_import = blender_module.importlib.import_module

    def blocked_import(name: str, package: str | None = None):
        if name in {"bpy", "mathutils"}:
            raise ModuleNotFoundError(name)
        return real_import(name, package)

    monkeypatch.setattr(blender_module.importlib, "import_module", blocked_import)

    with pytest.raises(BlenderUnavailableError, match="BlenderBackend requires"):
        BlenderBackend().create(Scene())
