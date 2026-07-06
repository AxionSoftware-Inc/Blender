import math
from types import SimpleNamespace

import bpy
from mathutils import Vector

from .math_parser import FormulaValidationError, compile_formula, detect_parameters, resolve_parameter_scope
from .scene_tools import ensure_material


SPECTRA_TAG = "spectra_object"


def ensure_graph_collection(context, collection_name="Spectra Graphs"):
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)
    return collection


def _link_object(collection, obj):
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)


def _time_value(context, settings):
    return context.scene.frame_current / max(settings.frame_rate_hint, 1.0)


def _curve_points(context, settings):
    parameter_scope = resolve_parameter_scope(context.scene.frame_current, settings)
    evaluator = compile_formula(settings.expression, ("x", "t", *parameter_scope.keys()))
    points = []
    step_count = max(2, settings.samples)
    span = settings.x_max - settings.x_min
    t_value = _time_value(context, settings)

    for index in range(step_count):
        factor = index / (step_count - 1)
        x = settings.x_min + span * factor
        y = evaluator(x=x, t=t_value, **parameter_scope)
        if not math.isfinite(y):
            continue
        points.append((x, y, 0.0))

    if len(points) < 2:
        raise FormulaValidationError("Formula did not generate enough valid points")
    return points


def _surface_geometry(context, settings):
    parameter_scope = resolve_parameter_scope(context.scene.frame_current, settings)
    evaluator = compile_formula(settings.expression, ("x", "y", "t", *parameter_scope.keys()))
    x_samples = max(2, settings.samples_x)
    y_samples = max(2, settings.samples_y)
    x_span = settings.x_max - settings.x_min
    y_span = settings.y_max - settings.y_min

    verts = []
    faces = []
    t_value = _time_value(context, settings)

    for yi in range(y_samples):
        y_factor = yi / (y_samples - 1)
        y = settings.y_min + y_span * y_factor
        for xi in range(x_samples):
            x_factor = xi / (x_samples - 1)
            x = settings.x_min + x_span * x_factor
            z = evaluator(x=x, y=y, t=t_value, **parameter_scope)
            if not math.isfinite(z):
                z = 0.0
            verts.append(Vector((x, y, z)))

    for yi in range(y_samples - 1):
        for xi in range(x_samples - 1):
            base = yi * x_samples + xi
            faces.append((base, base + 1, base + x_samples + 1, base + x_samples))
    return verts, faces


def _apply_curve_data(curve_data, points, settings):
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 24
    curve_data.bevel_depth = settings.curve_thickness

    while curve_data.splines:
        curve_data.splines.remove(curve_data.splines[0])

    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coordinates in zip(spline.points, points):
        point.co = (*coordinates, 1.0)

    material = ensure_material("SpectraCurveMaterial", (1.0, 0.76, 0.24, 1.0))
    curve_data.materials.clear()
    curve_data.materials.append(material)


def _apply_surface_data(mesh, verts, faces):
    mesh.clear_geometry()
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    material = ensure_material("SpectraSurfaceMaterial", (0.22, 0.58, 1.0, 1.0))
    mesh.materials.clear()
    mesh.materials.append(material)


def _apply_object_metadata(obj, settings, mode):
    obj[SPECTRA_TAG] = True
    obj["spectra_formula"] = settings.expression
    obj["spectra_mode"] = mode
    obj["spectra_scene_mode"] = settings.scene_mode
    obj["spectra_collection_name"] = settings.collection_name
    obj["spectra_x_min"] = settings.x_min
    obj["spectra_x_max"] = settings.x_max
    obj["spectra_y_min"] = settings.y_min
    obj["spectra_y_max"] = settings.y_max
    obj["spectra_samples"] = settings.samples
    obj["spectra_samples_x"] = settings.samples_x
    obj["spectra_samples_y"] = settings.samples_y
    obj["spectra_curve_thickness"] = settings.curve_thickness
    obj["spectra_frame_rate_hint"] = settings.frame_rate_hint
    obj["spectra_parameter_values"] = settings.parameter_values
    obj["spectra_live_formula_animation"] = settings.live_formula_animation
    obj["spectra_parameter_animation_enabled"] = settings.parameter_animation_enabled
    obj["spectra_animated_parameter"] = settings.animated_parameter
    obj["spectra_animated_parameter_start"] = settings.animated_parameter_start
    obj["spectra_animated_parameter_end"] = settings.animated_parameter_end
    obj["spectra_parameter_frame_start"] = settings.parameter_frame_start
    obj["spectra_parameter_frame_end"] = settings.parameter_frame_end
    obj["spectra_title_text"] = settings.title_text
    obj["spectra_formula_label"] = settings.formula_label
    obj["spectra_label_size"] = settings.label_size
    obj["spectra_show_labels"] = settings.show_labels


def build_curve_graph(context, settings):
    points = _curve_points(context, settings)

    curve_data = bpy.data.curves.new(name="SpectraCurve", type="CURVE")
    _apply_curve_data(curve_data, points, settings)

    obj = bpy.data.objects.new("SpectraCurve", curve_data)
    _apply_object_metadata(obj, settings, "CURVE_2D")

    collection = ensure_graph_collection(context, settings.collection_name)
    _link_object(collection, obj)
    return obj


def build_surface_graph(context, settings):
    verts, faces = _surface_geometry(context, settings)

    mesh = bpy.data.meshes.new("SpectraSurface")
    _apply_surface_data(mesh, verts, faces)

    obj = bpy.data.objects.new("SpectraSurface", mesh)
    _apply_object_metadata(obj, settings, "SURFACE_3D")

    collection = ensure_graph_collection(context, settings.collection_name)
    _link_object(collection, obj)
    return obj


def is_spectra_object(obj):
    return bool(obj and obj.get(SPECTRA_TAG))


def update_graph_object(context, obj, settings):
    if not is_spectra_object(obj):
        raise FormulaValidationError("Selected object is not a Spectra graph")

    expected_mode = settings.graph_mode
    current_mode = obj.get("spectra_mode")
    if current_mode != expected_mode:
        raise FormulaValidationError(
            f"Selected object mode is {current_mode}, but panel is set to {expected_mode}"
        )

    if obj.type == "CURVE" and expected_mode == "CURVE_2D":
        points = _curve_points(context, settings)
        _apply_curve_data(obj.data, points, settings)
    elif obj.type == "MESH" and expected_mode == "SURFACE_3D":
        verts, faces = _surface_geometry(context, settings)
        _apply_surface_data(obj.data, verts, faces)
    else:
        raise FormulaValidationError("Selected object type does not match graph mode")

    _apply_object_metadata(obj, settings, expected_mode)
    obj.name = "SpectraCurve" if expected_mode == "CURVE_2D" else "SpectraSurface"
    obj.data.name = obj.name
    return obj


def settings_from_object(obj):
    graph_mode = obj.get("spectra_mode", "CURVE_2D")
    scene_mode = obj.get("spectra_scene_mode", "MODE_2D")
    return SimpleNamespace(
        expression=obj.get("spectra_formula", "sin(x)"),
        graph_mode=graph_mode,
        scene_mode=scene_mode,
        collection_name=obj.get("spectra_collection_name", "Spectra Graphs"),
        x_min=float(obj.get("spectra_x_min", -6.0)),
        x_max=float(obj.get("spectra_x_max", 6.0)),
        y_min=float(obj.get("spectra_y_min", -6.0)),
        y_max=float(obj.get("spectra_y_max", 6.0)),
        samples=int(obj.get("spectra_samples", 128)),
        samples_x=int(obj.get("spectra_samples_x", 64)),
        samples_y=int(obj.get("spectra_samples_y", 64)),
        curve_thickness=float(obj.get("spectra_curve_thickness", 0.02)),
        frame_rate_hint=float(obj.get("spectra_frame_rate_hint", 24.0)),
        parameter_values=obj.get("spectra_parameter_values", ""),
        live_formula_animation=bool(obj.get("spectra_live_formula_animation", False)),
        parameter_animation_enabled=bool(obj.get("spectra_parameter_animation_enabled", False)),
        animated_parameter=obj.get("spectra_animated_parameter", "a"),
        animated_parameter_start=float(obj.get("spectra_animated_parameter_start", 0.0)),
        animated_parameter_end=float(obj.get("spectra_animated_parameter_end", 1.0)),
        parameter_frame_start=int(obj.get("spectra_parameter_frame_start", 1)),
        parameter_frame_end=int(obj.get("spectra_parameter_frame_end", 96)),
        title_text=obj.get("spectra_title_text", "Scientific Graph"),
        formula_label=obj.get("spectra_formula_label", ""),
        label_size=float(obj.get("spectra_label_size", 0.65)),
        show_labels=bool(obj.get("spectra_show_labels", True)),
    )
