from __future__ import annotations

from dataclasses import replace
from typing import Any

from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.primitives import PointCloud, Primitive, Surface
from spectra.core.scene import Scene
from spectra.core.types import Color

from .backend import _require_blender
from .incremental import IncrementalBlenderBackend, IncrementalBlenderHandle, _rebuild


_NATIVE_COLOR_ATTRIBUTE = "spectra_display_color"


def _visual_color_attribute(primitive: Primitive) -> VisualAttribute | None:
    association = None
    if isinstance(primitive, Surface):
        association = "vertex"
    elif isinstance(primitive, PointCloud):
        association = "instance"
    if association is None:
        return None

    candidates = tuple(
        attribute
        for attribute in primitive.attributes.attributes
        if attribute.kind == "color" and attribute.association == association
    )
    if not candidates:
        return None
    for attribute in candidates:
        if attribute.name == "display_color":
            return attribute
    return candidates[0]


def _sanitize_primitive(primitive: Primitive) -> Primitive:
    color_attribute = _visual_color_attribute(primitive)
    changes: dict[str, object] = {"attributes": VisualAttributeSet()}
    if isinstance(primitive, PointCloud) and color_attribute is not None:
        # Avoid the legacy material-slot color path. The quantitative adapter
        # realizes the explicit Scene v5 color attribute on the mesh instead.
        changes["colors"] = ()
    return replace(primitive, **changes)


def _sanitize_scene(scene: Scene) -> Scene:
    return replace(
        scene,
        primitives=tuple(_sanitize_primitive(primitive) for primitive in scene.primitives),
    )


def _quantitative_ids(scene: Scene) -> frozenset[str]:
    return frozenset(
        primitive.id
        for primitive in scene.primitives
        if _visual_color_attribute(primitive) is not None
    )


def _expanded_mesh_colors(
    primitive: Primitive,
    attribute: VisualAttribute,
) -> tuple[Color, ...]:
    colors = tuple(value for value in attribute.values if isinstance(value, Color))
    if len(colors) != len(attribute.values):
        raise TypeError(f"visual color attribute '{attribute.name}' contains a non-Color value")
    if isinstance(primitive, Surface):
        if len(colors) != len(primitive.vertices):
            raise ValueError("Surface vertex color attribute length mismatch")
        return colors
    if isinstance(primitive, PointCloud):
        if len(colors) != primitive.instance_count:
            raise ValueError("PointCloud instance color attribute length mismatch")
        return tuple(color for color in colors for _ in range(6))
    raise TypeError("quantitative mesh colors support Surface and PointCloud only")


def _write_mesh_color_attribute(mesh: Any, primitive: Primitive, colors: tuple[Color, ...]) -> None:
    color_attributes = getattr(mesh, "color_attributes", None)
    if color_attributes is None:
        raise RuntimeError("Blender mesh color attributes are unavailable")

    attribute = color_attributes.get(_NATIVE_COLOR_ATTRIBUTE)
    if attribute is not None:
        domain = getattr(attribute, "domain", None)
        data_type = getattr(attribute, "data_type", None)
        if domain != "POINT" or data_type not in {None, "FLOAT_COLOR"}:
            color_attributes.remove(attribute)
            attribute = None
    if attribute is None:
        attribute = color_attributes.new(
            name=_NATIVE_COLOR_ATTRIBUTE,
            type="FLOAT_COLOR",
            domain="POINT",
        )

    data = attribute.data
    if len(data) != len(colors):
        raise RuntimeError(
            "Blender mesh color-attribute size does not match Spectra vertex representation"
        )

    flat: list[float] = []
    for color in colors:
        flat.extend((color.r, color.g, color.b, color.a * primitive.opacity))
    try:
        data.foreach_set("color", flat)
    except (AttributeError, TypeError, ValueError):
        for item, color in zip(data, colors, strict=True):
            item.color = (
                color.r,
                color.g,
                color.b,
                color.a * primitive.opacity,
            )
    mesh.update()


def _configure_quantitative_material(
    bpy: Any,
    handle: IncrementalBlenderHandle,
    primitive: Primitive,
) -> Any:
    name = f"{handle.collection_name}::material::visual::{primitive.id}"
    material = bpy.data.materials.get(name)
    opacity = float(primitive.opacity)
    if material is not None and material.get("spectra_opacity") == opacity:
        handle.owned_material_names.add(material.name)
        return material

    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (1.0, 1.0, 1.0, opacity)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.attribute_name = _NATIVE_COLOR_ATTRIBUTE
    emission = nodes.new("ShaderNodeEmission")
    links.new(attribute.outputs["Color"], emission.inputs["Color"])
    emission.inputs["Strength"].default_value = 1.0

    shader_output = emission.outputs["Emission"]
    if opacity < 0.999999:
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = opacity
        links.new(transparent.outputs["BSDF"], mix.inputs[1])
        links.new(shader_output, mix.inputs[2])
        shader_output = mix.outputs["Shader"]
        if hasattr(material, "surface_render_method"):
            try:
                material.surface_render_method = "DITHERED"
            except (TypeError, ValueError):
                pass
        elif hasattr(material, "blend_method"):
            try:
                material.blend_method = "BLEND"
            except (TypeError, ValueError):
                pass

    links.new(shader_output, output.inputs["Surface"])
    material["spectra_opacity"] = opacity
    handle.owned_material_names.add(material.name)
    return material


def _apply_visual_attributes(handle: IncrementalBlenderHandle, scene: Scene) -> None:
    bpy, _ = _require_blender()
    for primitive in scene.primitives:
        attribute = _visual_color_attribute(primitive)
        if attribute is None:
            continue
        object_name = handle.object_names.get(primitive.id)
        native = bpy.data.objects.get(object_name) if object_name else None
        if native is None:
            raise RuntimeError(
                f"missing Blender object for quantitative primitive '{primitive.id}'"
            )
        mesh = getattr(native, "data", None)
        if mesh is None or not hasattr(mesh, "vertices"):
            raise RuntimeError(
                f"quantitative primitive '{primitive.id}' did not map to a Blender mesh"
            )
        colors = _expanded_mesh_colors(primitive, attribute)
        if len(colors) != len(mesh.vertices):
            raise RuntimeError(
                f"quantitative primitive '{primitive.id}' mesh representation size mismatch"
            )
        _write_mesh_color_attribute(mesh, primitive, colors)
        material = _configure_quantitative_material(bpy, handle, primitive)
        materials = getattr(mesh, "materials", None)
        if materials is not None:
            if len(materials) != 1 or materials[0] != material:
                materials.clear()
                materials.append(material)


class QuantitativeBlenderBackend(IncrementalBlenderBackend):
    """Incremental Blender backend with Scene-v5 mesh color realization.

    Surface vertex colors and PointCloud instance colors are carried as native
    Blender mesh color attributes instead of exploding quantitative values into
    many material slots. Scientific scalar-to-color mapping remains renderer
    neutral and happens before this backend.
    """

    name = "blender_quantitative"

    def create(self, scene: Scene) -> IncrementalBlenderHandle:
        sanitized = _sanitize_scene(scene)
        handle = super().create(sanitized)
        _apply_visual_attributes(handle, scene)
        handle._spectra_quantitative_ids = _quantitative_ids(scene)
        return handle

    def apply(self, handle: IncrementalBlenderHandle, scene: Scene) -> None:
        if handle.destroyed:
            raise RuntimeError("Blender handle is destroyed")
        sanitized = _sanitize_scene(scene)
        current_ids = _quantitative_ids(scene)
        previous_ids = getattr(handle, "_spectra_quantitative_ids", frozenset())
        if current_ids != previous_ids:
            bpy, _ = _require_blender()
            _rebuild(bpy, handle, sanitized)
        else:
            super().apply(handle, sanitized)
        _apply_visual_attributes(handle, scene)
        handle._spectra_quantitative_ids = current_ids


__all__ = ["QuantitativeBlenderBackend"]
