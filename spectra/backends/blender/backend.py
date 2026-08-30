from __future__ import annotations

from dataclasses import dataclass, field, replace
import importlib
import math
import uuid
from typing import Any

from spectra.backends.base import BackendCapabilities
from spectra.core.materials import Material
from spectra.core.primitives import (
    Camera,
    Group,
    Light,
    Point,
    Polyline,
    Primitive,
    Region,
    Surface,
    TextLabel,
    VectorGlyph,
)
from spectra.core.scene import Scene
from spectra.core.transforms import Transform3D
from spectra.core.types import Color


class BlenderUnavailableError(RuntimeError):
    """Raised when the Blender adapter is executed outside Blender Python."""


@dataclass
class BlenderHandle:
    """Native Blender resources owned by one backend session."""

    collection_name: str
    root_name: str
    owned_material_names: set[str] = field(default_factory=set)
    destroyed: bool = False


class BlenderBackend:
    """Reference Blender backend for static Spectra Scene snapshots.

    `bpy`/`mathutils` are imported lazily, so importing this package in normal
    Python remains safe. Timeline evaluation stays in Spectra; this backend sees
    only static Scene snapshots. `apply()` currently rebuilds the backend-owned
    collection deliberately. Incremental updates and dense GPU/native instancing
    come after this first architecture-proving vertical slice.
    """

    name = "blender"
    capabilities = BackendCapabilities(
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
                "light",
            }
        ),
        supports_group_hierarchy=True,
        supports_materials=True,
    )

    def create(self, scene: Scene) -> BlenderHandle:
        bpy, _ = _require_blender()
        token = uuid.uuid4().hex[:10]
        handle = BlenderHandle(
            collection_name=f"Spectra::{token}",
            root_name=f"SpectraRoot::{token}",
        )
        _populate_scene(bpy, handle, scene)
        return handle

    def apply(self, handle: BlenderHandle, scene: Scene) -> None:
        if handle.destroyed:
            raise RuntimeError("Blender handle is destroyed")
        bpy, _ = _require_blender()
        _remove_owned_scene(bpy, handle, keep_handle=True)
        _populate_scene(bpy, handle, scene)

    def destroy(self, handle: BlenderHandle) -> None:
        if handle.destroyed:
            return
        bpy, _ = _require_blender()
        _remove_owned_scene(bpy, handle, keep_handle=False)


def _require_blender() -> tuple[Any, Any]:
    try:
        bpy = importlib.import_module("bpy")
        mathutils = importlib.import_module("mathutils")
    except ModuleNotFoundError as exc:
        raise BlenderUnavailableError(
            "BlenderBackend requires execution inside Blender's Python environment"
        ) from exc
    return bpy, mathutils


def _frame_matrix(mathutils: Any, scene: Scene) -> Any:
    frame = scene.frame
    return mathutils.Matrix(
        (
            (frame.basis_x.x, frame.basis_y.x, frame.basis_z.x, frame.origin.x),
            (frame.basis_x.y, frame.basis_y.y, frame.basis_z.y, frame.origin.y),
            (frame.basis_x.z, frame.basis_y.z, frame.basis_z.z, frame.origin.z),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def _transform_matrix(mathutils: Any, transform: Transform3D) -> Any:
    translation = mathutils.Matrix.Translation(
        (transform.translation.x, transform.translation.y, transform.translation.z)
    )
    rotation = mathutils.Quaternion(
        (
            transform.rotation.w,
            transform.rotation.x,
            transform.rotation.y,
            transform.rotation.z,
        )
    ).to_matrix().to_4x4()
    scale = mathutils.Matrix.Diagonal(
        (transform.scale.x, transform.scale.y, transform.scale.z, 1.0)
    )
    return translation @ rotation @ scale


def _ensure_world_link(bpy: Any, collection: Any) -> None:
    scene_collection = bpy.context.scene.collection
    if collection.name not in {child.name for child in scene_collection.children}:
        scene_collection.children.link(collection)


def _populate_scene(bpy: Any, handle: BlenderHandle, scene: Scene) -> None:
    _, mathutils = _require_blender()
    collection = bpy.data.collections.get(handle.collection_name)
    if collection is None:
        collection = bpy.data.collections.new(handle.collection_name)
    _ensure_world_link(bpy, collection)

    root = bpy.data.objects.new(handle.root_name, None)
    root.empty_display_type = "PLAIN_AXES"
    root.matrix_world = _frame_matrix(mathutils, scene)
    collection.objects.link(root)

    material_sources = {material.id: material for material in scene.materials}
    material_map = {
        material.id: _create_material(bpy, handle, material)
        for material in scene.materials
    }

    object_map: dict[str, Any] = {}
    for primitive in scene.primitives:
        object_map[primitive.id] = _create_primitive(
            bpy,
            mathutils,
            handle,
            collection,
            root,
            primitive,
            material_sources,
            material_map,
        )

    # Group currently means organizational references in Core. We intentionally
    # do not parent children under the Group Empty: doing so would invent transform
    # inheritance semantics not yet owned by the generic Scene graph.
    active_camera = scene.active_camera()
    if active_camera is not None:
        native_camera = object_map.get(active_camera.id)
        if native_camera is not None:
            bpy.context.scene.camera = native_camera


def _create_primitive(
    bpy: Any,
    mathutils: Any,
    handle: BlenderHandle,
    collection: Any,
    root: Any,
    primitive: Primitive,
    material_sources: dict[str, Material],
    material_map: dict[str, Any],
) -> Any:
    if isinstance(primitive, Point):
        obj = _create_point(bpy, collection, primitive)
    elif isinstance(primitive, Polyline):
        obj = _create_polyline(bpy, collection, primitive)
    elif isinstance(primitive, Surface):
        obj = _create_surface(bpy, collection, primitive)
    elif isinstance(primitive, Region):
        obj = _create_region(bpy, collection, primitive)
    elif isinstance(primitive, VectorGlyph):
        obj = _create_vector_glyph(bpy, collection, primitive)
    elif isinstance(primitive, TextLabel):
        obj = _create_text(bpy, collection, primitive)
    elif isinstance(primitive, Group):
        obj = bpy.data.objects.new(_object_name(primitive), None)
        obj.empty_display_type = "PLAIN_AXES"
        collection.objects.link(obj)
    elif isinstance(primitive, Camera):
        obj = _create_camera(bpy, collection, primitive)
    elif isinstance(primitive, Light):
        obj = _create_light(bpy, collection, primitive)
    else:
        raise TypeError(f"unsupported Blender primitive: {type(primitive).__qualname__}")

    obj.parent = root
    local_matrix = _transform_matrix(mathutils, primitive.transform)
    if isinstance(primitive, TextLabel):
        local_matrix = local_matrix @ mathutils.Matrix.Translation(
            (primitive.position.x, primitive.position.y, primitive.position.z)
        )
    obj.matrix_local = local_matrix
    obj.hide_viewport = not primitive.visible
    obj.hide_render = not primitive.visible

    native_material = _resolve_material(
        bpy,
        handle,
        primitive,
        material_sources,
        material_map,
    )
    if native_material is not None and getattr(obj, "data", None) is not None:
        materials = getattr(obj.data, "materials", None)
        if materials is not None:
            materials.append(native_material)
    return obj


def _object_name(primitive: Primitive) -> str:
    return f"Spectra::{primitive.id}"


def _create_point(bpy: Any, collection: Any, point: Point) -> Any:
    r = point.radius
    c = point.position
    vertices = [
        (c.x + r, c.y, c.z),
        (c.x - r, c.y, c.z),
        (c.x, c.y + r, c.z),
        (c.x, c.y - r, c.z),
        (c.x, c.y, c.z + r),
        (c.x, c.y, c.z - r),
    ]
    faces = [
        (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
        (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5),
    ]
    mesh = bpy.data.meshes.new(f"{_object_name(point)}::mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(_object_name(point), mesh)
    collection.objects.link(obj)
    return obj


def _visible_polyline_points(polyline: Polyline) -> tuple[Any, ...]:
    if polyline.trim_start <= 0.0 and polyline.trim_end >= 1.0:
        return polyline.points
    total = len(polyline.points)
    start = min(total - 2, max(0, int(math.floor(polyline.trim_start * (total - 1)))))
    end = min(total - 1, max(start + 1, int(math.ceil(polyline.trim_end * (total - 1)))))
    return polyline.points[start : end + 1]


def _create_polyline(bpy: Any, collection: Any, polyline: Polyline) -> Any:
    points = _visible_polyline_points(polyline)
    curve = bpy.data.curves.new(f"{_object_name(polyline)}::curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = max(polyline.width * 0.5, 0.0)
    curve.bevel_resolution = 1
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, native in zip(points, spline.points, strict=True):
        native.co = (point.x, point.y, point.z, 1.0)
    spline.use_cyclic_u = polyline.closed and len(points) == len(polyline.points)
    obj = bpy.data.objects.new(_object_name(polyline), curve)
    collection.objects.link(obj)
    return obj


def _create_surface(bpy: Any, collection: Any, surface: Surface) -> Any:
    mesh = bpy.data.meshes.new(f"{_object_name(surface)}::mesh")
    mesh.from_pydata(
        [(v.x, v.y, v.z) for v in surface.vertices],
        [],
        list(surface.triangles),
    )
    mesh.update()
    obj = bpy.data.objects.new(_object_name(surface), mesh)
    collection.objects.link(obj)
    return obj


def _create_region(bpy: Any, collection: Any, region: Region) -> Any:
    mesh = bpy.data.meshes.new(f"{_object_name(region)}::mesh")
    vertices = [(p.x, p.y, p.z) for p in region.boundary]
    mesh.from_pydata(vertices, [], [tuple(range(len(vertices)))])
    mesh.update()
    obj = bpy.data.objects.new(_object_name(region), mesh)
    collection.objects.link(obj)
    return obj


def _create_vector_glyph(bpy: Any, collection: Any, glyph: VectorGlyph) -> Any:
    endpoint = glyph.origin + glyph.vector
    curve = bpy.data.curves.new(f"{_object_name(glyph)}::curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.01
    curve.bevel_resolution = 1
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (glyph.origin.x, glyph.origin.y, glyph.origin.z, 1.0)
    spline.points[1].co = (endpoint.x, endpoint.y, endpoint.z, 1.0)
    obj = bpy.data.objects.new(_object_name(glyph), curve)
    collection.objects.link(obj)
    return obj


def _create_text(bpy: Any, collection: Any, label: TextLabel) -> Any:
    curve = bpy.data.curves.new(f"{_object_name(label)}::text", "FONT")
    curve.body = label.text
    curve.size = label.size
    obj = bpy.data.objects.new(_object_name(label), curve)
    collection.objects.link(obj)
    return obj


def _create_camera(bpy: Any, collection: Any, camera: Camera) -> Any:
    data = bpy.data.cameras.new(f"{_object_name(camera)}::camera")
    if camera.projection == "perspective":
        data.type = "PERSP"
        data.angle_y = camera.fov_y_radians
    else:
        data.type = "ORTHO"
        data.ortho_scale = camera.orthographic_scale
    data.clip_start = camera.near_clip
    data.clip_end = camera.far_clip
    obj = bpy.data.objects.new(_object_name(camera), data)
    collection.objects.link(obj)
    return obj


def _create_light(bpy: Any, collection: Any, light: Light) -> Any:
    type_map = {
        "ambient": "AREA",
        "directional": "SUN",
        "point": "POINT",
        "spot": "SPOT",
    }
    data = bpy.data.lights.new(f"{_object_name(light)}::light", type_map[light.light_type])
    data.color = (light.color.r, light.color.g, light.color.b)
    data.energy = light.intensity if light.light_type == "directional" else light.intensity * 100.0
    if hasattr(data, "cutoff_distance"):
        data.cutoff_distance = light.range
    if light.light_type == "ambient" and hasattr(data, "shape"):
        data.shape = "DISK"
        data.size = max(light.range, 1.0)
    if light.light_type == "spot":
        data.spot_size = light.spot_angle_radians
    obj = bpy.data.objects.new(_object_name(light), data)
    collection.objects.link(obj)
    return obj


def _primitive_color(primitive: Primitive) -> Color | None:
    return getattr(primitive, "color", None)


def _resolve_material(
    bpy: Any,
    handle: BlenderHandle,
    primitive: Primitive,
    material_sources: dict[str, Material],
    material_map: dict[str, Any],
) -> Any | None:
    if primitive.material_id is not None:
        if primitive.opacity >= 0.999999:
            return material_map[primitive.material_id]
        source = material_sources[primitive.material_id]
        derived = replace(
            source,
            id=f"{source.id}::opacity::{primitive.id}",
            base_color=Color(
                source.base_color.r,
                source.base_color.g,
                source.base_color.b,
                source.base_color.a * primitive.opacity,
            ),
        )
        return _create_material(bpy, handle, derived)

    color = _primitive_color(primitive)
    if color is None:
        return None
    fallback = Material(
        id=f"primitive::{primitive.id}",
        base_color=Color(color.r, color.g, color.b, color.a * primitive.opacity),
        shading="unlit",
    )
    return _create_material(bpy, handle, fallback)


def _create_material(bpy: Any, handle: BlenderHandle, material: Material) -> Any:
    name = f"{handle.collection_name}::material::{material.id}"
    native = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    native.use_nodes = True
    native.diffuse_color = (
        material.base_color.r,
        material.base_color.g,
        material.base_color.b,
        material.base_color.a,
    )
    nodes = native.node_tree.nodes
    links = native.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")

    if material.shading == "unlit":
        shader = nodes.new("ShaderNodeEmission")
        shader.inputs["Color"].default_value = (
            material.base_color.r,
            material.base_color.g,
            material.base_color.b,
            1.0,
        )
        shader.inputs["Strength"].default_value = max(1.0, material.emission_strength)
        shader_output = shader.outputs["Emission"]
    else:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Base Color"].default_value = (
            material.base_color.r,
            material.base_color.g,
            material.base_color.b,
            1.0,
        )
        if "Metallic" in shader.inputs:
            shader.inputs["Metallic"].default_value = material.metallic
        if "Roughness" in shader.inputs:
            shader.inputs["Roughness"].default_value = material.roughness
        if "Emission Color" in shader.inputs:
            shader.inputs["Emission Color"].default_value = (
                material.emission_color.r,
                material.emission_color.g,
                material.emission_color.b,
                1.0,
            )
        elif "Emission" in shader.inputs:
            shader.inputs["Emission"].default_value = (
                material.emission_color.r,
                material.emission_color.g,
                material.emission_color.b,
                1.0,
            )
        if "Emission Strength" in shader.inputs:
            shader.inputs["Emission Strength"].default_value = material.emission_strength
        shader_output = shader.outputs["BSDF"]

    alpha = material.base_color.a
    if alpha < 0.999999:
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = alpha
        links.new(transparent.outputs["BSDF"], mix.inputs[1])
        links.new(shader_output, mix.inputs[2])
        links.new(mix.outputs["Shader"], output.inputs["Surface"])
        if hasattr(native, "surface_render_method"):
            try:
                native.surface_render_method = "DITHERED"
            except (TypeError, ValueError):
                pass
        elif hasattr(native, "blend_method"):
            try:
                native.blend_method = "BLEND"
            except (TypeError, ValueError):
                pass
    else:
        links.new(shader_output, output.inputs["Surface"])

    handle.owned_material_names.add(native.name)
    return native


def _remove_owned_scene(bpy: Any, handle: BlenderHandle, *, keep_handle: bool) -> None:
    collection = bpy.data.collections.get(handle.collection_name)
    if collection is not None:
        for obj in list(collection.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and getattr(data, "users", 0) == 0:
                _remove_datablock(bpy, data)
        bpy.data.collections.remove(collection)

    for material_name in list(handle.owned_material_names):
        material = bpy.data.materials.get(material_name)
        if material is not None and material.users == 0:
            bpy.data.materials.remove(material)
    handle.owned_material_names.clear()

    if not keep_handle:
        handle.destroyed = True


def _remove_datablock(bpy: Any, data: Any) -> None:
    for collection_name in ("meshes", "curves", "cameras", "lights"):
        collection = getattr(bpy.data, collection_name)
        try:
            collection.remove(data)
            return
        except (TypeError, ReferenceError):
            continue
