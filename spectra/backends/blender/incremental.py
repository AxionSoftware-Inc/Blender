from __future__ import annotations

from dataclasses import dataclass, field, replace
import uuid
from typing import Any

from spectra.backends.base import BackendCapabilities
from spectra.core.materials import Material
from spectra.core.primitives import (
    Camera,
    Group,
    Light,
    Point,
    PointCloud,
    Polyline,
    Primitive,
    Surface,
    TextLabel,
    VectorGlyphSet,
)
from spectra.core.scene import Scene

from .backend import (
    BlenderUnavailableError,
    _create_material,
    _create_primitive,
    _ensure_world_link,
    _frame_matrix,
    _octahedron_geometry,
    _remove_datablock,
    _remove_owned_scene,
    _require_blender,
    _transform_matrix,
    _visible_polyline_points,
)


@dataclass
class IncrementalBlenderHandle:
    """Stable native-object mapping for realtime Spectra playback in Blender."""

    collection_name: str
    root_name: str
    object_names: dict[str, str] = field(default_factory=dict)
    owned_material_names: set[str] = field(default_factory=set)
    last_scene: Scene | None = None
    destroyed: bool = False


class IncrementalBlenderBackend:
    """Blender backend that preserves native objects across Scene snapshots.

    Spectra still owns time: this backend receives static `Scene.sample(t)`
    snapshots. Stable Spectra primitive IDs map to stable Blender objects. When
    possible, frequently-changing numeric buffers (particle positions, wave
    polylines, vector fields, surface vertices) are updated in-place. Structural
    changes fall back to a deterministic rebuild without changing Core/domain
    semantics.
    """

    name = "blender"
    capabilities = BackendCapabilities(
        frozenset(
            {
                "point",
                "point_cloud",
                "polyline",
                "surface",
                "region",
                "vector_glyph",
                "vector_glyph_set",
                "text",
                "group",
                "camera",
                "light",
            }
        ),
        supports_group_hierarchy=True,
        supports_materials=True,
    )

    def create(self, scene: Scene) -> IncrementalBlenderHandle:
        bpy, _ = _require_blender()
        token = uuid.uuid4().hex[:10]
        handle = IncrementalBlenderHandle(
            collection_name=f"Spectra::{token}",
            root_name=f"SpectraRoot::{token}",
        )
        _populate_incremental(bpy, handle, scene)
        handle.last_scene = scene
        return handle

    def apply(self, handle: IncrementalBlenderHandle, scene: Scene) -> None:
        if handle.destroyed:
            raise RuntimeError("Blender handle is destroyed")
        bpy, mathutils = _require_blender()
        previous = handle.last_scene
        if previous is None or not _structure_compatible(previous, scene):
            _rebuild(bpy, handle, scene)
            return

        collection = bpy.data.collections.get(handle.collection_name)
        root = bpy.data.objects.get(handle.root_name)
        if collection is None or root is None:
            _rebuild(bpy, handle, scene)
            return

        root.matrix_world = _frame_matrix(mathutils, scene)
        material_sources = {material.id: material for material in scene.materials}
        material_map = {
            material.id: _create_material(bpy, handle, material)
            for material in scene.materials
        }

        for old, new in zip(previous.primitives, scene.primitives, strict=True):
            if old == new:
                continue
            object_name = handle.object_names.get(new.id)
            native = bpy.data.objects.get(object_name) if object_name else None
            if native is None:
                _rebuild(bpy, handle, scene)
                return

            if _common_only_change(old, new):
                _apply_common(mathutils, native, new)
                continue
            if _fast_update_point(native, old, new):
                _apply_common(mathutils, native, new)
                continue
            if _fast_update_point_cloud(native, old, new):
                _apply_common(mathutils, native, new)
                continue
            if _fast_update_polyline(native, old, new):
                _apply_common(mathutils, native, new)
                continue
            if _fast_update_surface(native, old, new):
                _apply_common(mathutils, native, new)
                continue
            if _fast_update_vector_glyph_set(native, old, new):
                _apply_common(mathutils, native, new)
                continue
            if _fast_update_text(native, old, new):
                _apply_common(mathutils, native, new)
                continue

            _replace_native_primitive(
                bpy,
                mathutils,
                handle,
                collection,
                root,
                native,
                new,
                material_sources,
                material_map,
            )

        active_camera = scene.active_camera()
        if active_camera is not None:
            object_name = handle.object_names.get(active_camera.id)
            native_camera = bpy.data.objects.get(object_name) if object_name else None
            if native_camera is not None:
                bpy.context.scene.camera = native_camera
        elif previous.active_camera_id is not None:
            previous_name = handle.object_names.get(previous.active_camera_id)
            if (
                previous_name is not None
                and bpy.context.scene.camera is not None
                and bpy.context.scene.camera.name == previous_name
            ):
                bpy.context.scene.camera = None

        handle.last_scene = scene

    def destroy(self, handle: IncrementalBlenderHandle) -> None:
        if handle.destroyed:
            return
        bpy, _ = _require_blender()
        _remove_owned_scene(bpy, handle, keep_handle=False)
        handle.object_names.clear()
        handle.last_scene = None


def _structure_compatible(previous: Scene, current: Scene) -> bool:
    if len(previous.primitives) != len(current.primitives):
        return False
    for old, new in zip(previous.primitives, current.primitives, strict=True):
        if old.id != new.id or type(old) is not type(new):
            return False
    return {material.id for material in previous.materials} == {
        material.id for material in current.materials
    }


def _populate_incremental(
    bpy: Any,
    handle: IncrementalBlenderHandle,
    scene: Scene,
) -> None:
    _, mathutils = _require_blender()
    collection = bpy.data.collections.get(handle.collection_name)
    if collection is None:
        collection = bpy.data.collections.new(handle.collection_name)
    _ensure_world_link(bpy, collection)

    root = bpy.data.objects.get(handle.root_name)
    if root is None:
        root = bpy.data.objects.new(handle.root_name, None)
        root.empty_display_type = "PLAIN_AXES"
        collection.objects.link(root)
    root.matrix_world = _frame_matrix(mathutils, scene)

    material_sources = {material.id: material for material in scene.materials}
    material_map = {
        material.id: _create_material(bpy, handle, material)
        for material in scene.materials
    }

    handle.object_names.clear()
    for primitive in scene.primitives:
        native = _create_primitive(
            bpy,
            mathutils,
            handle,
            collection,
            root,
            primitive,
            material_sources,
            material_map,
        )
        handle.object_names[primitive.id] = native.name

    active_camera = scene.active_camera()
    if active_camera is not None:
        native_name = handle.object_names.get(active_camera.id)
        native_camera = bpy.data.objects.get(native_name) if native_name else None
        if native_camera is not None:
            bpy.context.scene.camera = native_camera


def _rebuild(bpy: Any, handle: IncrementalBlenderHandle, scene: Scene) -> None:
    _remove_owned_scene(bpy, handle, keep_handle=True)
    handle.object_names.clear()
    _populate_incremental(bpy, handle, scene)
    handle.last_scene = scene


def _common_only_change(previous: Primitive, current: Primitive) -> bool:
    if type(previous) is not type(current):
        return False
    normalized = replace(
        previous,
        visible=current.visible,
        transform=current.transform,
    )
    return normalized == current


def _apply_common(mathutils: Any, native: Any, primitive: Primitive) -> None:
    matrix = _transform_matrix(mathutils, primitive.transform)
    if isinstance(primitive, TextLabel):
        matrix = matrix @ mathutils.Matrix.Translation(
            (primitive.position.x, primitive.position.y, primitive.position.z)
        )
    native.matrix_local = matrix
    native.hide_viewport = not primitive.visible
    native.hide_render = not primitive.visible


def _same_except(previous: Primitive, current: Primitive, **changes: Any) -> bool:
    if type(previous) is not type(current):
        return False
    values = {
        "visible": current.visible,
        "transform": current.transform,
        **changes,
    }
    return replace(previous, **values) == current


def _fast_update_point(native: Any, previous: Primitive, current: Primitive) -> bool:
    if not isinstance(previous, Point) or not isinstance(current, Point):
        return False
    if not _same_except(previous, current, position=current.position):
        return False
    mesh = getattr(native, "data", None)
    if mesh is None or len(getattr(mesh, "vertices", ())) != 6:
        return False
    vertices, _ = _octahedron_geometry(
        current.position.x,
        current.position.y,
        current.position.z,
        current.radius,
    )
    for vertex, coordinates in zip(mesh.vertices, vertices, strict=True):
        vertex.co = coordinates
    mesh.update()
    return True


def _fast_update_point_cloud(native: Any, previous: Primitive, current: Primitive) -> bool:
    if not isinstance(previous, PointCloud) or not isinstance(current, PointCloud):
        return False
    if not _same_except(previous, current, positions=current.positions):
        return False
    mesh = getattr(native, "data", None)
    expected_vertices = current.instance_count * 6
    if mesh is None or len(getattr(mesh, "vertices", ())) != expected_vertices:
        return False

    cursor = 0
    for index, position in enumerate(current.positions):
        radius = current.radii[index] if current.radii else current.radius
        local_vertices, _ = _octahedron_geometry(
            position.x,
            position.y,
            position.z,
            radius,
        )
        for coordinates in local_vertices:
            mesh.vertices[cursor].co = coordinates
            cursor += 1
    mesh.update()
    return True


def _fast_update_polyline(native: Any, previous: Primitive, current: Primitive) -> bool:
    if not isinstance(previous, Polyline) or not isinstance(current, Polyline):
        return False
    if not _same_except(previous, current, points=current.points):
        return False

    previous_visible = _visible_polyline_points(previous)
    current_visible = _visible_polyline_points(current)
    if len(previous_visible) != len(current_visible):
        return False

    curve = getattr(native, "data", None)
    splines = getattr(curve, "splines", None) if curve is not None else None
    if splines is None or len(splines) != 1:
        return False
    spline = splines[0]
    if len(spline.points) != len(current_visible):
        return False
    for native_point, point in zip(spline.points, current_visible, strict=True):
        native_point.co = (point.x, point.y, point.z, 1.0)
    return True


def _fast_update_surface(native: Any, previous: Primitive, current: Primitive) -> bool:
    if not isinstance(previous, Surface) or not isinstance(current, Surface):
        return False
    if not _same_except(previous, current, vertices=current.vertices):
        return False
    mesh = getattr(native, "data", None)
    if mesh is None or len(getattr(mesh, "vertices", ())) != len(current.vertices):
        return False
    for vertex, value in zip(mesh.vertices, current.vertices, strict=True):
        vertex.co = (value.x, value.y, value.z)
    mesh.update()
    return True


def _fast_update_vector_glyph_set(
    native: Any,
    previous: Primitive,
    current: Primitive,
) -> bool:
    if not isinstance(previous, VectorGlyphSet) or not isinstance(current, VectorGlyphSet):
        return False
    if not _same_except(
        previous,
        current,
        origins=current.origins,
        vectors=current.vectors,
    ):
        return False
    curve = getattr(native, "data", None)
    splines = getattr(curve, "splines", None) if curve is not None else None
    if splines is None or len(splines) != current.instance_count:
        return False
    for spline, origin, vector in zip(
        splines,
        current.origins,
        current.vectors,
        strict=True,
    ):
        if len(spline.points) != 2:
            return False
        endpoint = origin + vector
        spline.points[0].co = (origin.x, origin.y, origin.z, 1.0)
        spline.points[1].co = (endpoint.x, endpoint.y, endpoint.z, 1.0)
    return True


def _fast_update_text(native: Any, previous: Primitive, current: Primitive) -> bool:
    if not isinstance(previous, TextLabel) or not isinstance(current, TextLabel):
        return False
    if not _same_except(previous, current, position=current.position):
        return False
    return True


def _replace_native_primitive(
    bpy: Any,
    mathutils: Any,
    handle: IncrementalBlenderHandle,
    collection: Any,
    root: Any,
    native: Any,
    primitive: Primitive,
    material_sources: dict[str, Material],
    material_map: dict[str, Any],
) -> None:
    """Replace only one primitive's data while preserving its native object identity."""
    temporary = _create_primitive(
        bpy,
        mathutils,
        handle,
        collection,
        root,
        primitive,
        material_sources,
        material_map,
    )

    old_data = getattr(native, "data", None)
    new_data = getattr(temporary, "data", None)
    if new_data is not None:
        native.data = new_data

    native.matrix_local = temporary.matrix_local.copy()
    native.hide_viewport = temporary.hide_viewport
    native.hide_render = temporary.hide_render

    bpy.data.objects.remove(temporary, do_unlink=True)
    if old_data is not None and getattr(old_data, "users", 0) == 0:
        _remove_datablock(bpy, old_data)
