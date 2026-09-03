from __future__ import annotations

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.backends.blender.quantitative import (
    _expanded_mesh_colors,
    _sanitize_scene,
)
from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.primitives import PointCloud, Surface, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3


def _color_attribute(association: str, count: int) -> VisualAttribute:
    return VisualAttribute(
        name="display_color",
        association=association,
        kind="color",
        values=tuple(
            Color(index / max(count - 1, 1), 0.25, 1.0 - index / max(count - 1, 1))
            for index in range(count)
        ),
    )


def test_quantitative_backend_imports_without_blender() -> None:
    backend = QuantitativeBlenderBackend()
    assert backend.name == "blender_quantitative"
    assert "surface" in backend.capabilities.primitive_kinds
    assert "point_cloud" in backend.capabilities.primitive_kinds


def test_quantitative_scene_sanitization_preserves_geometry() -> None:
    colors = _color_attribute("vertex", 3)
    surface = Surface(
        id="surface",
        vertices=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0)),
        triangles=((0, 1, 2),),
        attributes=VisualAttributeSet((colors,)),
    )
    sanitized = _sanitize_scene(Scene(primitives=(surface,))).get("surface")
    assert sanitized.vertices == surface.vertices
    assert sanitized.triangles == surface.triangles
    assert not sanitized.attributes


def test_point_cloud_quantitative_path_avoids_legacy_material_colors() -> None:
    display = _color_attribute("instance", 2)
    cloud = PointCloud(
        id="cloud",
        positions=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
        colors=tuple(display.values),
        attributes=VisualAttributeSet((display,)),
    )
    sanitized = _sanitize_scene(Scene(primitives=(cloud,))).get("cloud")
    assert sanitized.positions == cloud.positions
    assert sanitized.colors == ()
    assert not sanitized.attributes

    expanded = _expanded_mesh_colors(cloud, display)
    assert len(expanded) == 12
    assert expanded[:6] == (display.values[0],) * 6
    assert expanded[6:] == (display.values[1],) * 6


def test_vector_glyph_set_keeps_curve_color_fallback() -> None:
    display = _color_attribute("instance", 2)
    glyphs = VectorGlyphSet(
        id="vectors",
        origins=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
        vectors=(Vec3(0.0, 1.0, 0.0), Vec3(0.0, 1.0, 0.0)),
        colors=tuple(display.values),
        attributes=VisualAttributeSet((display,)),
    )
    sanitized = _sanitize_scene(Scene(primitives=(glyphs,))).get("vectors")
    assert sanitized.colors == glyphs.colors
    assert not sanitized.attributes
