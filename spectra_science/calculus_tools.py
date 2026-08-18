import bpy
import math
from mathutils import Vector

from .graph_builders import ensure_graph_collection, is_spectra_object, math_to_world, settings_from_object
from .math_parser import FormulaValidationError, compile_formula, resolve_parameter_scope
from .scene_tools import ensure_material, ensure_guide_collection


CALCULUS_TAG = "spectra_calculus"


def _time_value(context, settings):
    return context.scene.frame_current / max(settings.frame_rate_hint, 1.0)


def _animated_x_value(context, settings):
    frame_start = min(settings.calculus_frame_start, settings.calculus_frame_end)
    frame_end = max(settings.calculus_frame_start, settings.calculus_frame_end)
    if not settings.animate_calculus_x:
        return settings.calculus_x
    if frame_end == frame_start:
        return settings.calculus_x_end
    frame = min(max(context.scene.frame_current, frame_start), frame_end)
    factor = (frame - frame_start) / (frame_end - frame_start)
    return settings.calculus_x_start + (settings.calculus_x_end - settings.calculus_x_start) * factor


def _animated_h_value(context, settings):
    if not getattr(settings, "animate_secant_h", False):
        return settings.calculus_h
    frame_start = min(settings.secant_frame_start, settings.secant_frame_end)
    frame_end = max(settings.secant_frame_start, settings.secant_frame_end)
    if frame_end == frame_start:
        return settings.secant_h_end
    frame = min(max(context.scene.frame_current, frame_start), frame_end)
    factor = (frame - frame_start) / (frame_end - frame_start)
    return settings.secant_h_start + (settings.secant_h_end - settings.secant_h_start) * factor


def _animated_limit_distance(context, settings):
    if not getattr(settings, "animate_limit", False):
        return max(getattr(settings, "limit_distance_end", 0.05), 1e-5)
    frame_start = min(settings.limit_frame_start, settings.limit_frame_end)
    frame_end = max(settings.limit_frame_start, settings.limit_frame_end)
    if frame_end == frame_start:
        return max(settings.limit_distance_end, 1e-5)
    frame = min(max(context.scene.frame_current, frame_start), frame_end)
    factor = (frame - frame_start) / (frame_end - frame_start)
    return max(
        settings.limit_distance_start + (settings.limit_distance_end - settings.limit_distance_start) * factor,
        1e-5,
    )


def _curve_evaluator(context, settings):
    parameter_scope = resolve_parameter_scope(context.scene.frame_current, settings)
    evaluator = compile_formula(settings.expression, ("x", "t", *parameter_scope.keys()))
    return evaluator, parameter_scope


def curve_value(context, settings, x_value):
    evaluator, parameter_scope = _curve_evaluator(context, settings)
    y_value = evaluator(x=x_value, t=_time_value(context, settings), **parameter_scope)
    if not isinstance(y_value, (int, float)):
        raise FormulaValidationError("Curve formula must resolve to a real number")
    return float(y_value)


def safe_curve_value(context, settings, x_value):
    try:
        value = curve_value(context, settings, x_value)
    except Exception:
        return None
    return value if math.isfinite(value) else None


def curve_point(context, settings, x_value):
    return Vector(math_to_world(settings, x_value, curve_value(context, settings, x_value), 0.0))


def curve_slope(context, settings, x_value):
    dx = max(1e-4, abs(settings.x_max - settings.x_min) / max(settings.samples, 32) * 0.25)
    y1 = curve_value(context, settings, x_value - dx)
    y2 = curve_value(context, settings, x_value + dx)
    return (y2 - y1) / (2.0 * dx)


def clamp_x_value(settings, x_value):
    x_min = min(settings.x_min, settings.x_max)
    x_max = max(settings.x_min, settings.x_max)
    return min(max(x_value, x_min), x_max)


def _ensure_calculus_collection(context):
    return ensure_graph_collection(context, "Spectra Calculus")


def _ensure_calculus_label_collection(context):
    return ensure_guide_collection(context, "Spectra Calculus Labels")


def _metadata(obj, graph_obj, role):
    obj[CALCULUS_TAG] = True
    obj["spectra_calculus_role"] = role
    obj["spectra_calculus_graph"] = graph_obj.name
    obj["spectra_role"] = role


def _find_child(collection, graph_name, role):
    expected_name = f"{graph_name}_{role}"
    for obj in collection.objects:
        if (
            obj.get("spectra_calculus_graph") == graph_name
            and obj.get("spectra_calculus_role") == role
        ) or obj.name == expected_name:
            return obj
    return None


def _ensure_line_object(collection, graph_obj, role, color):
    obj = _find_child(collection, graph_obj.name, role)
    if obj and obj.type == "CURVE":
        _metadata(obj, graph_obj, role)
        return obj
    curve_data = bpy.data.curves.new(name=f"{graph_obj.name}_{role}", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = 0.025
    spline = curve_data.splines.new("POLY")
    spline.points.add(1)
    obj = bpy.data.objects.new(f"{graph_obj.name}_{role}", curve_data)
    curve_data.materials.append(ensure_material(f"Spectra{role}Material", color))
    collection.objects.link(obj)
    _metadata(obj, graph_obj, role)
    return obj


def _set_line_points(obj, start, end):
    spline = obj.data.splines[0]
    spline.points[0].co = (*start, 1.0)
    spline.points[1].co = (*end, 1.0)


def _ensure_point_object(collection, graph_obj):
    obj = _find_child(collection, graph_obj.name, "MOVING_POINT")
    if obj and obj.type == "MESH":
        _metadata(obj, graph_obj, "MOVING_POINT")
        return obj
    mesh = bpy.data.meshes.new(f"{graph_obj.name}_MovingPoint")
    obj = bpy.data.objects.new(f"{graph_obj.name}_MovingPoint", mesh)
    collection.objects.link(obj)
    _metadata(obj, graph_obj, "MOVING_POINT")
    material = ensure_material("SpectraPointMaterial", (1.0, 0.42, 0.42, 1.0))
    mesh.materials.append(material)
    return obj


def _ensure_text_object(collection, graph_obj, role, size, location):
    obj = _find_child(collection, graph_obj.name, role)
    if obj and obj.type == "FONT":
        _metadata(obj, graph_obj, role)
        return obj
    curve = bpy.data.curves.new(name=f"{graph_obj.name}_{role}", type="FONT")
    curve.size = size
    curve.align_x = "LEFT"
    curve.align_y = "CENTER"
    curve.materials.append(ensure_material("SpectraDerivativeTextMaterial", (0.98, 0.98, 1.0, 1.0)))
    obj = bpy.data.objects.new(f"{graph_obj.name}_{role}", curve)
    obj.location = location
    collection.objects.link(obj)
    _metadata(obj, graph_obj, role)
    return obj


def _apply_point_geometry(obj, radius):
    mesh = obj.data
    mesh.clear_geometry()
    verts = [
        (-radius, 0.0, 0.0),
        (radius, 0.0, 0.0),
        (0.0, -radius, 0.0),
        (0.0, radius, 0.0),
        (0.0, 0.0, -radius),
        (0.0, 0.0, radius),
    ]
    edges = [
        (0, 2), (2, 1), (1, 3), (3, 0),
        (0, 4), (4, 1), (1, 5), (5, 0),
        (2, 4), (4, 3), (3, 5), (5, 2),
    ]
    mesh.from_pydata(verts, edges, [])
    mesh.update()


def _ensure_area_object(collection, graph_obj):
    obj = _find_child(collection, graph_obj.name, "AREA")
    if obj and obj.type == "MESH":
        _metadata(obj, graph_obj, "AREA")
        return obj
    mesh = bpy.data.meshes.new(f"{graph_obj.name}_Area")
    obj = bpy.data.objects.new(f"{graph_obj.name}_Area", mesh)
    collection.objects.link(obj)
    _metadata(obj, graph_obj, "AREA")
    material = ensure_material("SpectraAreaMaterial", (0.22, 0.9, 0.6, 0.45))
    material.blend_method = "BLEND"
    mesh.materials.append(material)
    return obj


def _ensure_derivative_curve_object(collection, graph_obj):
    obj = _find_child(collection, graph_obj.name, "DERIVATIVE_GRAPH")
    if obj and obj.type == "CURVE":
        _metadata(obj, graph_obj, "DERIVATIVE_GRAPH")
        return obj
    curve_data = bpy.data.curves.new(name=f"{graph_obj.name}_Derivative", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 18
    curve_data.bevel_depth = 0.018
    obj = bpy.data.objects.new(f"{graph_obj.name}_Derivative", curve_data)
    curve_data.materials.append(ensure_material("SpectraDerivativeGraphMaterial", (0.92, 0.4, 1.0, 1.0)))
    collection.objects.link(obj)
    _metadata(obj, graph_obj, "DERIVATIVE_GRAPH")
    return obj


def _ensure_derivative_point_object(collection, graph_obj):
    obj = _find_child(collection, graph_obj.name, "DERIVATIVE_POINT")
    if obj and obj.type == "MESH":
        _metadata(obj, graph_obj, "DERIVATIVE_POINT")
        return obj
    mesh = bpy.data.meshes.new(f"{graph_obj.name}_DerivativePoint")
    obj = bpy.data.objects.new(f"{graph_obj.name}_DerivativePoint", mesh)
    collection.objects.link(obj)
    _metadata(obj, graph_obj, "DERIVATIVE_POINT")
    material = ensure_material("SpectraDerivativePointMaterial", (0.98, 0.45, 1.0, 1.0))
    mesh.materials.append(material)
    return obj


def _apply_area_mesh(obj, points):
    mesh = obj.data
    mesh.clear_geometry()
    verts = [(x, y, 0.0) for x, y in points]
    verts.extend([(x, 0.0, 0.0) for x, _ in reversed(points)])
    faces = [tuple(range(len(verts)))] if len(verts) >= 3 else []
    mesh.from_pydata(verts, [], faces)
    mesh.update()


def _apply_curve_points(curve_data, points):
    while curve_data.splines:
        curve_data.splines.remove(curve_data.splines[0])
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (*coords, 1.0)


def _update_derivative_graph(context, collection, graph_obj, graph_settings, panel_settings):
    derivative_obj = _ensure_derivative_curve_object(collection, graph_obj)
    step_count = max(8, min(graph_settings.samples, 1024))
    span = graph_settings.x_max - graph_settings.x_min
    points = []
    for index in range(step_count):
        factor = index / (step_count - 1)
        x_value = graph_settings.x_min + span * factor
        slope = curve_slope(context, graph_settings, x_value) * panel_settings.derivative_graph_scale_y
        points.append(math_to_world(graph_settings, x_value, slope + panel_settings.derivative_graph_offset_y, 0.0))
    _apply_curve_points(derivative_obj.data, points)
    derivative_obj.hide_viewport = not panel_settings.show_derivative_graph
    derivative_obj.hide_render = not panel_settings.show_derivative_graph
    slope_at_x0 = curve_slope(context, graph_settings, _animated_x_value(context, panel_settings))
    derivative_point = _ensure_derivative_point_object(collection, graph_obj)
    _apply_point_geometry(derivative_point, panel_settings.calculus_point_size * 0.8)
    derivative_point.location = (
        *math_to_world(
            graph_settings,
            _animated_x_value(context, panel_settings),
            slope_at_x0 * panel_settings.derivative_graph_scale_y + panel_settings.derivative_graph_offset_y,
            0.0,
        ),
    )
    derivative_point.hide_viewport = not panel_settings.show_derivative_graph
    derivative_point.hide_render = not panel_settings.show_derivative_graph
    return derivative_obj, derivative_point


def _set_marker(scene, name, frame):
    marker = scene.timeline_markers.get(name)
    if marker is None:
        marker = scene.timeline_markers.new(name=name, frame=frame)
    marker.frame = frame


def _update_timeline_markers(scene, settings):
    if not settings.animate_calculus_x:
        pass
    else:
        _set_marker(scene, "Spectra x0 Start", settings.calculus_frame_start)
        _set_marker(scene, "Spectra x0 End", settings.calculus_frame_end)
    if getattr(settings, "animate_secant_h", False):
        _set_marker(scene, "Spectra h Start", settings.secant_frame_start)
        _set_marker(scene, "Spectra h End", settings.secant_frame_end)
    if getattr(settings, "integral_animation_mode", "NONE") != "NONE":
        _set_marker(scene, "Spectra Integral Start", settings.integral_frame_start)
        _set_marker(scene, "Spectra Integral End", settings.integral_frame_end)
    if getattr(settings, "animate_limit", False):
        _set_marker(scene, "Spectra Limit Start", settings.limit_frame_start)
        _set_marker(scene, "Spectra Limit End", settings.limit_frame_end)


def _format_float(value):
    return f"{value:.4f}"


def _tangent_formula_text(x_value, y_value, slope):
    intercept = y_value - slope * x_value
    return f"T(x) = {_format_float(slope)}x + {_format_float(intercept)}"


def _ensure_angle_guide(collection, graph_obj):
    return _ensure_line_object(collection, graph_obj, "ANGLE_GUIDE", (1.0, 0.82, 0.25, 1.0))


def _ensure_integral_point_object(collection, graph_obj, role, color):
    obj = _find_child(collection, graph_obj.name, role)
    if obj and obj.type == "MESH":
        _metadata(obj, graph_obj, role)
        return obj
    mesh = bpy.data.meshes.new(f"{graph_obj.name}_{role}")
    obj = bpy.data.objects.new(f"{graph_obj.name}_{role}", mesh)
    collection.objects.link(obj)
    _metadata(obj, graph_obj, role)
    mesh.materials.append(ensure_material(f"Spectra{role}Material", color))
    return obj


def _ensure_integral_mesh_object(collection, graph_obj, role, color):
    obj = _find_child(collection, graph_obj.name, role)
    if obj and obj.type == "MESH":
        _metadata(obj, graph_obj, role)
        return obj
    mesh = bpy.data.meshes.new(f"{graph_obj.name}_{role}")
    obj = bpy.data.objects.new(f"{graph_obj.name}_{role}", mesh)
    collection.objects.link(obj)
    _metadata(obj, graph_obj, role)
    material = ensure_material(f"Spectra{role}Material", color)
    material.blend_method = "BLEND"
    mesh.materials.append(material)
    return obj


def _ensure_integral_curve_object(collection, graph_obj, role, color, thickness=0.02):
    obj = _find_child(collection, graph_obj.name, role)
    if obj and obj.type == "CURVE":
        _metadata(obj, graph_obj, role)
        return obj
    curve_data = bpy.data.curves.new(name=f"{graph_obj.name}_{role}", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 10
    curve_data.bevel_depth = thickness
    spline = curve_data.splines.new("POLY")
    spline.points.add(1)
    obj = bpy.data.objects.new(f"{graph_obj.name}_{role}", curve_data)
    curve_data.materials.append(ensure_material(f"Spectra{role}Material", color))
    collection.objects.link(obj)
    _metadata(obj, graph_obj, role)
    return obj


def _ensure_limit_point_object(collection, graph_obj, role, color):
    return _ensure_integral_point_object(collection, graph_obj, role, color)


def _ensure_limit_curve_object(collection, graph_obj, role, color, thickness=0.018):
    return _ensure_integral_curve_object(collection, graph_obj, role, color, thickness=thickness)


def _limit_positions(context, graph_settings, panel_settings):
    x0 = clamp_x_value(graph_settings, panel_settings.limit_target_x)
    distance = _animated_limit_distance(context, panel_settings)
    return (
        x0,
        clamp_x_value(graph_settings, x0 - distance),
        clamp_x_value(graph_settings, x0 + distance),
    )


def _estimate_limit_side(context, graph_settings, x0, side, base_distance):
    working_distance = min(max(base_distance * 0.12, 0.03), 0.18)
    samples = []
    for factor in (1.0, 0.5, 0.25, 0.125, 0.0625):
        sample_x = x0 + working_distance * factor * side
        sample_x = clamp_x_value(graph_settings, sample_x)
        if abs(sample_x - x0) < 1e-8:
            continue
        y_value = safe_curve_value(context, graph_settings, sample_x)
        if y_value is not None:
            samples.append(y_value)
    if not samples:
        return None
    return sum(samples[-min(3, len(samples)):]) / min(3, len(samples))


def _describe_limit_value(left_value, right_value, tolerance, mode):
    if mode == "LEFT_ONLY":
        if left_value is None:
            return "DNE"
        return _format_float(left_value)
    if mode == "RIGHT_ONLY":
        if right_value is None:
            return "DNE"
        return _format_float(right_value)
    if left_value is None or right_value is None:
        return "DNE"
    if abs(left_value - right_value) > tolerance:
        return "DNE"
    return _format_float((left_value + right_value) * 0.5)


def _limit_hud_items(graph_settings, panel_settings, x0, left_x, right_x, left_y, right_y, limit_text):
    def fmt(value):
        return _format_float(value) if value is not None else "undefined"

    mode_label = {
        "TWO_SIDED": "two-sided",
        "LEFT_ONLY": "left-sided",
        "RIGHT_ONLY": "right-sided",
    }.get(panel_settings.limit_mode, "two-sided")
    items = [
        ("LIMIT_TITLE", panel_settings.title_text or "Limit Visualizer", math_to_world(graph_settings, -8.7, 7.85, 0.0), panel_settings.limit_hud_scale * 1.08),
        ("LIMIT_TARGET", f"x -> {_format_float(x0)} ({mode_label})", math_to_world(graph_settings, -8.7, 7.0, 0.0), panel_settings.limit_hud_scale),
        ("LIMIT_LEFT", f"left: x={_format_float(left_x)}  f(x)={fmt(left_y)}", math_to_world(graph_settings, -8.7, 6.2, 0.0), panel_settings.limit_hud_scale * 0.96),
        ("LIMIT_RIGHT", f"right: x={_format_float(right_x)}  f(x)={fmt(right_y)}", math_to_world(graph_settings, -8.7, 5.45, 0.0), panel_settings.limit_hud_scale * 0.96),
        ("LIMIT_VALUE", f"lim f(x) = {limit_text}", math_to_world(graph_settings, -8.7, 4.65, 0.0), panel_settings.limit_hud_scale),
    ]
    return items


def _normalized_frame_factor(frame_current, frame_start, frame_end):
    start = min(frame_start, frame_end)
    end = max(frame_start, frame_end)
    if end == start:
        return 1.0
    frame = min(max(frame_current, start), end)
    return (frame - start) / (end - start)


def integral_bounds(context, settings):
    mode = getattr(settings, "integral_animation_mode", "NONE")
    a = settings.integral_a
    b = settings.integral_b
    if mode != "NONE":
        factor = _normalized_frame_factor(
            context.scene.frame_current,
            settings.integral_frame_start,
            settings.integral_frame_end,
        )
        if mode == "UPPER":
            b = settings.integral_upper_start + (settings.integral_upper_end - settings.integral_upper_start) * factor
        elif mode == "BOTH":
            a = settings.integral_lower_start + (settings.integral_lower_end - settings.integral_lower_start) * factor
            b = settings.integral_upper_start + (settings.integral_upper_end - settings.integral_upper_start) * factor
    return a, b


def clamp_bound_pair(settings, a, b):
    x_min = min(settings.x_min, settings.x_max)
    x_max = max(settings.x_min, settings.x_max)
    a_clamped = min(max(a, x_min), x_max)
    b_clamped = min(max(b, x_min), x_max)
    return a_clamped, b_clamped


def integrate_trapezoid(context, settings, a, b, sample_count):
    if a == b:
        return 0.0
    steps = max(2, int(sample_count))
    direction = 1.0 if b >= a else -1.0
    lo, hi = (a, b) if a <= b else (b, a)
    dx = (hi - lo) / (steps - 1)
    total = 0.0
    prev_x = lo
    prev_y = curve_value(context, settings, prev_x)
    for index in range(1, steps):
        x = lo + dx * index
        y = curve_value(context, settings, x)
        total += 0.5 * (prev_y + y) * (x - prev_x)
        prev_x = x
        prev_y = y
    return total * direction


def integrate_absolute_trapezoid(context, settings, a, b, sample_count):
    if a == b:
        return 0.0
    steps = max(2, int(sample_count))
    lo, hi = (a, b) if a <= b else (b, a)
    dx = (hi - lo) / (steps - 1)
    total = 0.0
    prev_x = lo
    prev_y = abs(curve_value(context, settings, prev_x))
    for index in range(1, steps):
        x = lo + dx * index
        y = abs(curve_value(context, settings, x))
        total += 0.5 * (prev_y + y) * (x - prev_x)
        prev_x = x
        prev_y = y
    return total


def build_curve_sample_cache(context, settings, sample_count):
    steps = max(8, int(sample_count))
    span = settings.x_max - settings.x_min
    xs = []
    ys = []
    prefix_signed = []
    prefix_absolute = []
    signed_total = 0.0
    absolute_total = 0.0
    prev_x = None
    prev_y = None

    for index in range(steps):
        factor = index / (steps - 1)
        x = settings.x_min + span * factor
        y = safe_curve_value(context, settings, x)
        xs.append(x)
        ys.append(y)
        if prev_x is not None and prev_y is not None and y is not None:
            dx = x - prev_x
            signed_total += 0.5 * (prev_y + y) * dx
            absolute_total += 0.5 * (abs(prev_y) + abs(y)) * dx
        prefix_signed.append(signed_total)
        prefix_absolute.append(absolute_total)
        prev_x = x
        prev_y = y

    return {
        "xs": xs,
        "ys": ys,
        "prefix_signed": prefix_signed,
        "prefix_absolute": prefix_absolute,
    }


def _prefix_value_at(cache, x_value, absolute=False):
    xs = cache["xs"]
    prefix = cache["prefix_absolute"] if absolute else cache["prefix_signed"]
    if x_value <= xs[0]:
        return prefix[0]
    if x_value >= xs[-1]:
        return prefix[-1]
    for index in range(1, len(xs)):
        left_x = xs[index - 1]
        right_x = xs[index]
        if x_value <= right_x:
            span = right_x - left_x
            if span <= 0.0:
                return prefix[index]
            factor = (x_value - left_x) / span
            return prefix[index - 1] + (prefix[index] - prefix[index - 1]) * factor
    return prefix[-1]


def integrate_from_cache(cache, a, b, absolute=False):
    if a == b:
        return 0.0
    direction = 1.0 if b >= a else -1.0
    lo, hi = (a, b) if a <= b else (b, a)
    return (_prefix_value_at(cache, hi, absolute=absolute) - _prefix_value_at(cache, lo, absolute=absolute)) * direction


def _add_polygon(mesh_data, math_points, graph_settings):
    start_index = len(mesh_data["verts"])
    for x, y in math_points:
        mesh_data["verts"].append(math_to_world(graph_settings, x, y, 0.0))
    mesh_data["faces"].append(tuple(range(start_index, start_index + len(math_points))))


def _append_signed_segment(pos_data, neg_data, graph_settings, x1, y1, x2, y2):
    if y1 >= 0.0 and y2 >= 0.0:
        _add_polygon(pos_data, [(x1, 0.0), (x1, y1), (x2, y2), (x2, 0.0)], graph_settings)
        return
    if y1 <= 0.0 and y2 <= 0.0:
        _add_polygon(neg_data, [(x1, 0.0), (x1, y1), (x2, y2), (x2, 0.0)], graph_settings)
        return
    if y2 == y1:
        return
    cross_x = x1 + ((0.0 - y1) * (x2 - x1) / (y2 - y1))
    if y1 > 0.0:
        _add_polygon(pos_data, [(x1, 0.0), (x1, y1), (cross_x, 0.0)], graph_settings)
        _add_polygon(neg_data, [(cross_x, 0.0), (x2, y2), (x2, 0.0)], graph_settings)
    else:
        _add_polygon(neg_data, [(x1, 0.0), (x1, y1), (cross_x, 0.0)], graph_settings)
        _add_polygon(pos_data, [(cross_x, 0.0), (x2, y2), (x2, 0.0)], graph_settings)


def _apply_mesh_data(obj, mesh_data):
    mesh = obj.data
    mesh.clear_geometry()
    mesh.from_pydata(mesh_data["verts"], [], mesh_data["faces"])
    mesh.update()


def _integral_hud_items(graph_settings, panel_settings, a, b, signed_value, absolute_value):
    delta = b - a
    sign_word = "positive" if signed_value >= 0.0 else "negative"
    items = [
        ("INTEGRAL_TITLE", panel_settings.title_text or "Integral Visualizer", math_to_world(graph_settings, -8.7, 7.85, 0.0), panel_settings.integral_hud_scale * 1.08),
        ("INTEGRAL_A", f"a = {_format_float(a)}", math_to_world(graph_settings, -8.7, 7.0, 0.0), panel_settings.integral_hud_scale),
        ("INTEGRAL_B", f"b = {_format_float(b)}", math_to_world(graph_settings, -8.7, 6.25, 0.0), panel_settings.integral_hud_scale),
        ("INTEGRAL_DELTA", f"Delta x = {_format_float(delta)}", math_to_world(graph_settings, -8.7, 5.5, 0.0), panel_settings.integral_hud_scale),
    ]
    if panel_settings.integral_value_mode == "ABSOLUTE":
        items.append(
            ("INTEGRAL_VALUE", f"Abs area = {_format_float(absolute_value)}", math_to_world(graph_settings, -8.7, 4.75, 0.0), panel_settings.integral_hud_scale * 0.95)
        )
    elif panel_settings.integral_value_mode == "SIGNED":
        items.append(
            ("INTEGRAL_VALUE", f"Int_a^b f(x)dx = {_format_float(signed_value)}", math_to_world(graph_settings, -8.7, 4.75, 0.0), panel_settings.integral_hud_scale * 0.95)
        )
    else:
        items.append(
            ("INTEGRAL_VALUE", f"Signed = {_format_float(signed_value)}", math_to_world(graph_settings, -8.7, 4.75, 0.0), panel_settings.integral_hud_scale * 0.95)
        )
        items.append(
            ("INTEGRAL_ABS", f"Absolute = {_format_float(absolute_value)}", math_to_world(graph_settings, -8.7, 4.05, 0.0), panel_settings.integral_hud_scale * 0.9)
        )
    items.append(
        ("INTEGRAL_SIGN", f"Signed area: {sign_word}", math_to_world(graph_settings, -8.7, 3.35 if panel_settings.integral_value_mode == 'BOTH' else 4.05, 0.0), panel_settings.integral_hud_scale * 0.9)
    )
    return items


def _update_derivative_hud(context, graph_obj, graph_settings, panel_settings, point_math, slope):
    label_collection = _ensure_calculus_label_collection(context)
    if not panel_settings.derivative_show_hud:
        for role in ("HUD_TITLE", "HUD_POINT", "HUD_SLOPE", "HUD_ANGLE", "HUD_TANGENT"):
            obj = _find_child(label_collection, graph_obj.name, role)
            if obj:
                obj.hide_viewport = True
                obj.hide_render = True
        return

    hud_scale = panel_settings.derivative_hud_scale
    angle_degrees = math.degrees(math.atan(slope))
    x_text = _format_float(point_math.x)
    y_text = _format_float(point_math.y)
    slope_text = _format_float(slope)
    angle_text = _format_float(angle_degrees)
    h_text = _format_float(_animated_h_value(context, panel_settings))

    items = [
        ("HUD_TITLE", panel_settings.title_text or "Derivative Visualizer", math_to_world(graph_settings, -8.7, 7.85, 0.0), hud_scale * 1.1, None),
        ("HUD_POINT", f"P = ({x_text}, {y_text})", math_to_world(graph_settings, -8.7, 7.0, 0.0), hud_scale, None),
        ("HUD_SLOPE", f"f'(x0) = {slope_text}", math_to_world(graph_settings, -8.7, 6.2, 0.0), hud_scale, None),
        ("HUD_ANGLE", f"angle = {angle_text} deg   h = {h_text}", math_to_world(graph_settings, -8.7, 5.4, 0.0), hud_scale, None),
        ("HUD_TANGENT", _tangent_formula_text(point_math.x, point_math.y, slope), math_to_world(graph_settings, -8.7, 4.55, 0.0), hud_scale * 0.92, None),
    ]

    for role, fallback_text, location, size, title_override in items:
        obj = _ensure_text_object(label_collection, graph_obj, role, size, location)
        obj.data.size = size
        obj.location = location
        if role == "HUD_POINT":
            obj.data.body = fallback_text if panel_settings.derivative_show_point_label else ""
        elif role == "HUD_TANGENT":
            obj.data.body = fallback_text if panel_settings.derivative_show_tangent_formula else ""
        else:
            obj.data.body = title_override or fallback_text
        obj.hide_viewport = False
        obj.hide_render = False


def _update_point_label(context, graph_obj, graph_settings, panel_settings, point_world, point_math):
    label_collection = _ensure_calculus_label_collection(context)
    obj = _ensure_text_object(
        label_collection,
        graph_obj,
        "POINT_LABEL",
        panel_settings.derivative_hud_scale * 0.7,
        (
            point_world.x + graph_settings.coordinate_unit_scale * 0.3,
            point_world.y + graph_settings.coordinate_unit_scale * 0.45,
            0.0,
        ),
    )
    obj.data.size = panel_settings.derivative_hud_scale * 0.7
    obj.location = (
        point_world.x + graph_settings.coordinate_unit_scale * 0.3,
        point_world.y + graph_settings.coordinate_unit_scale * 0.45,
        0.0,
    )
    obj.data.body = f"({_format_float(point_math.x)}, {_format_float(point_math.y)})" if panel_settings.derivative_show_point_label else ""
    obj.hide_viewport = not panel_settings.derivative_show_point_label
    obj.hide_render = not panel_settings.derivative_show_point_label


def create_or_update_calculus_visuals(context, graph_obj, panel_settings):
    if not is_spectra_object(graph_obj):
        raise FormulaValidationError("Select a Spectra curve graph first")
    graph_settings = settings_from_object(graph_obj)
    if graph_settings.graph_mode != "CURVE_2D":
        raise FormulaValidationError("Calculus visuals currently work on 2D curve graphs only")

    collection = _ensure_calculus_collection(context)
    x0 = clamp_x_value(graph_settings, _animated_x_value(context, panel_settings))
    h = _animated_h_value(context, panel_settings)
    p1_x = clamp_x_value(graph_settings, x0 + h)
    y0 = curve_value(context, graph_settings, x0)
    y1 = curve_value(context, graph_settings, p1_x)
    p0_math = Vector((x0, y0, 0.0))
    p0 = Vector(math_to_world(graph_settings, x0, y0, 0.0))
    p1 = Vector(math_to_world(graph_settings, p1_x, y1, 0.0))
    slope = curve_slope(context, graph_settings, x0)
    span_math = panel_settings.calculus_line_span

    helpers = []

    if panel_settings.show_moving_point:
        point_obj = _ensure_point_object(collection, graph_obj)
        _apply_point_geometry(point_obj, panel_settings.calculus_point_size)
        point_obj.location = p0
        point_obj.hide_viewport = False
        point_obj.hide_render = False
        helpers.append(point_obj)

    if panel_settings.show_secant:
        secant = _ensure_line_object(collection, graph_obj, "SECANT", (0.3, 0.85, 1.0, 1.0))
        _set_line_points(secant, p0, p1)
        secant.hide_viewport = False
        secant.hide_render = False
        helpers.append(secant)

    if panel_settings.show_tangent:
        tangent = _ensure_line_object(collection, graph_obj, "TANGENT", (1.0, 0.35, 0.35, 1.0))
        tangent_start = Vector(math_to_world(graph_settings, x0 - span_math, y0 - slope * span_math, 0.0))
        tangent_end = Vector(math_to_world(graph_settings, x0 + span_math, y0 + slope * span_math, 0.0))
        _set_line_points(tangent, tangent_start, tangent_end)
        tangent.hide_viewport = False
        tangent.hide_render = False
        helpers.append(tangent)

        if panel_settings.derivative_show_angle_guide:
            angle_guide = _ensure_angle_guide(collection, graph_obj)
            guide_end = Vector(math_to_world(graph_settings, x0 + span_math * 0.9, y0, 0.0))
            _set_line_points(angle_guide, p0, guide_end)
            angle_guide.hide_viewport = False
            angle_guide.hide_render = False
            helpers.append(angle_guide)

    if panel_settings.show_area:
        area_obj = _ensure_area_object(collection, graph_obj)
        area_start = min(panel_settings.area_x_min, panel_settings.area_x_max)
        area_end = max(panel_settings.area_x_min, panel_settings.area_x_max)
        sample_count = max(8, min(panel_settings.area_samples, 512))
        area_points = []
        for index in range(sample_count):
            factor = index / (sample_count - 1)
            x_value = area_start + (area_end - area_start) * factor
            point = curve_point(context, graph_settings, x_value)
            area_points.append((point.x, point.y))
        _apply_area_mesh(area_obj, area_points)
        area_obj.hide_viewport = False
        area_obj.hide_render = False
        helpers.append(area_obj)

    derivative_obj, derivative_point = _update_derivative_graph(context, collection, graph_obj, graph_settings, panel_settings)
    helpers.append(derivative_obj)
    helpers.append(derivative_point)

    update_calculus_metadata(graph_obj, panel_settings)
    _update_timeline_markers(context.scene, panel_settings)
    _update_derivative_hud(context, graph_obj, graph_settings, panel_settings, p0_math, slope)
    _update_point_label(context, graph_obj, graph_settings, panel_settings, p0, p0_math)
    hide_unused_calculus_objects(collection, graph_obj.name, panel_settings)
    return helpers


def hide_unused_calculus_objects(collection, graph_name, settings):
    visibility = {
        "MOVING_POINT": settings.show_moving_point,
        "SECANT": settings.show_secant,
        "TANGENT": settings.show_tangent,
        "AREA": settings.show_area,
        "ANGLE_GUIDE": settings.show_tangent and settings.derivative_show_angle_guide,
        "DERIVATIVE_GRAPH": settings.show_derivative_graph,
        "DERIVATIVE_POINT": settings.show_derivative_graph,
    }
    for obj in collection.objects:
        if obj.get("spectra_calculus_graph") != graph_name:
            continue
        role = obj.get("spectra_calculus_role")
        if role not in visibility:
            continue
        visible = visibility[role]
        obj.hide_viewport = not visible
        obj.hide_render = not visible


def update_calculus_metadata(graph_obj, settings):
    graph_obj["spectra_active_template"] = getattr(settings, "active_template", "CUSTOM")
    graph_obj["spectra_calculus_enabled"] = any(
        (
            settings.show_moving_point,
            settings.show_secant,
            settings.show_tangent,
            settings.show_area,
            settings.show_derivative_graph,
            settings.derivative_show_hud,
            settings.derivative_show_point_label,
        )
    )
    graph_obj["spectra_calculus_x"] = settings.calculus_x
    graph_obj["spectra_calculus_h"] = settings.calculus_h
    graph_obj["spectra_calculus_line_span"] = settings.calculus_line_span
    graph_obj["spectra_show_moving_point"] = settings.show_moving_point
    graph_obj["spectra_show_secant"] = settings.show_secant
    graph_obj["spectra_show_tangent"] = settings.show_tangent
    graph_obj["spectra_show_area"] = settings.show_area
    graph_obj["spectra_area_x_min"] = settings.area_x_min
    graph_obj["spectra_area_x_max"] = settings.area_x_max
    graph_obj["spectra_area_samples"] = settings.area_samples
    graph_obj["spectra_animate_calculus_x"] = settings.animate_calculus_x
    graph_obj["spectra_calculus_x_start"] = settings.calculus_x_start
    graph_obj["spectra_calculus_x_end"] = settings.calculus_x_end
    graph_obj["spectra_calculus_frame_start"] = settings.calculus_frame_start
    graph_obj["spectra_calculus_frame_end"] = settings.calculus_frame_end
    graph_obj["spectra_calculus_point_size"] = settings.calculus_point_size
    graph_obj["spectra_derivative_show_hud"] = settings.derivative_show_hud
    graph_obj["spectra_derivative_show_tangent_formula"] = settings.derivative_show_tangent_formula
    graph_obj["spectra_derivative_show_point_label"] = settings.derivative_show_point_label
    graph_obj["spectra_derivative_show_angle_guide"] = settings.derivative_show_angle_guide
    graph_obj["spectra_derivative_hud_scale"] = settings.derivative_hud_scale
    graph_obj["spectra_limit_enabled"] = any(
        (
            settings.show_limit_guides,
            settings.show_limit_hud,
            settings.limit_show_hole,
            settings.limit_show_target_point,
            settings.animate_limit,
        )
    )
    graph_obj["spectra_limit_target_x"] = settings.limit_target_x
    graph_obj["spectra_limit_mode"] = settings.limit_mode
    graph_obj["spectra_animate_limit"] = settings.animate_limit
    graph_obj["spectra_limit_distance_start"] = settings.limit_distance_start
    graph_obj["spectra_limit_distance_end"] = settings.limit_distance_end
    graph_obj["spectra_limit_frame_start"] = settings.limit_frame_start
    graph_obj["spectra_limit_frame_end"] = settings.limit_frame_end
    graph_obj["spectra_limit_estimate_tolerance"] = settings.limit_estimate_tolerance
    graph_obj["spectra_show_limit_guides"] = settings.show_limit_guides
    graph_obj["spectra_show_limit_hud"] = settings.show_limit_hud
    graph_obj["spectra_limit_hud_scale"] = settings.limit_hud_scale
    graph_obj["spectra_limit_show_hole"] = settings.limit_show_hole
    graph_obj["spectra_limit_hole_y"] = settings.limit_hole_y
    graph_obj["spectra_limit_show_target_point"] = settings.limit_show_target_point
    graph_obj["spectra_limit_target_point_y"] = settings.limit_target_point_y
    graph_obj["spectra_show_derivative_graph"] = settings.show_derivative_graph
    graph_obj["spectra_derivative_graph_offset_y"] = settings.derivative_graph_offset_y
    graph_obj["spectra_derivative_graph_scale_y"] = settings.derivative_graph_scale_y
    graph_obj["spectra_animate_secant_h"] = settings.animate_secant_h
    graph_obj["spectra_secant_h_start"] = settings.secant_h_start
    graph_obj["spectra_secant_h_end"] = settings.secant_h_end
    graph_obj["spectra_secant_frame_start"] = settings.secant_frame_start
    graph_obj["spectra_secant_frame_end"] = settings.secant_frame_end
    graph_obj["spectra_integral_enabled"] = any(
        (
            settings.show_integral_area,
            settings.show_integral_hud,
            settings.integral_show_accumulation_graph,
            settings.integral_show_strip_preview,
            settings.integral_scene_mode in {"ACCUMULATION", "FTC"},
        )
    )
    graph_obj["spectra_integral_a"] = settings.integral_a
    graph_obj["spectra_integral_b"] = settings.integral_b
    graph_obj["spectra_integral_samples"] = settings.integral_samples
    graph_obj["spectra_show_integral_area"] = settings.show_integral_area
    graph_obj["spectra_show_integral_bound_lines"] = settings.show_integral_bound_lines
    graph_obj["spectra_show_integral_bound_points"] = settings.show_integral_bound_points
    graph_obj["spectra_show_integral_hud"] = settings.show_integral_hud
    graph_obj["spectra_integral_hud_scale"] = settings.integral_hud_scale
    graph_obj["spectra_integral_scene_mode"] = settings.integral_scene_mode
    graph_obj["spectra_integral_value_mode"] = settings.integral_value_mode
    graph_obj["spectra_integral_animation_mode"] = settings.integral_animation_mode
    graph_obj["spectra_integral_lower_start"] = settings.integral_lower_start
    graph_obj["spectra_integral_lower_end"] = settings.integral_lower_end
    graph_obj["spectra_integral_upper_start"] = settings.integral_upper_start
    graph_obj["spectra_integral_upper_end"] = settings.integral_upper_end
    graph_obj["spectra_integral_frame_start"] = settings.integral_frame_start
    graph_obj["spectra_integral_frame_end"] = settings.integral_frame_end
    graph_obj["spectra_integral_show_accumulation_graph"] = settings.integral_show_accumulation_graph
    graph_obj["spectra_integral_graph_offset_y"] = settings.integral_graph_offset_y
    graph_obj["spectra_integral_graph_scale_y"] = settings.integral_graph_scale_y
    graph_obj["spectra_integral_show_strip_preview"] = settings.integral_show_strip_preview
    graph_obj["spectra_integral_strip_count"] = settings.integral_strip_count


def calculus_settings_from_object(obj):
    return type(
        "CalculusSettings",
        (),
        {
            "calculus_x": float(obj.get("spectra_calculus_x", 0.0)),
            "calculus_h": float(obj.get("spectra_calculus_h", 1.0)),
            "calculus_line_span": float(obj.get("spectra_calculus_line_span", 1.75)),
            "show_moving_point": bool(obj.get("spectra_show_moving_point", True)),
            "show_secant": bool(obj.get("spectra_show_secant", True)),
            "show_tangent": bool(obj.get("spectra_show_tangent", True)),
            "show_area": bool(obj.get("spectra_show_area", False)),
            "area_x_min": float(obj.get("spectra_area_x_min", -2.0)),
            "area_x_max": float(obj.get("spectra_area_x_max", 2.0)),
            "area_samples": int(obj.get("spectra_area_samples", 64)),
            "animate_calculus_x": bool(obj.get("spectra_animate_calculus_x", False)),
            "calculus_x_start": float(obj.get("spectra_calculus_x_start", -3.0)),
            "calculus_x_end": float(obj.get("spectra_calculus_x_end", 3.0)),
            "calculus_frame_start": int(obj.get("spectra_calculus_frame_start", 1)),
            "calculus_frame_end": int(obj.get("spectra_calculus_frame_end", 96)),
            "calculus_point_size": float(obj.get("spectra_calculus_point_size", 0.18)),
            "derivative_show_hud": bool(obj.get("spectra_derivative_show_hud", True)),
            "derivative_show_tangent_formula": bool(obj.get("spectra_derivative_show_tangent_formula", True)),
            "derivative_show_point_label": bool(obj.get("spectra_derivative_show_point_label", True)),
            "derivative_show_angle_guide": bool(obj.get("spectra_derivative_show_angle_guide", True)),
            "derivative_hud_scale": float(obj.get("spectra_derivative_hud_scale", 0.58)),
            "limit_target_x": float(obj.get("spectra_limit_target_x", 1.0)),
            "limit_mode": obj.get("spectra_limit_mode", "TWO_SIDED"),
            "animate_limit": bool(obj.get("spectra_animate_limit", False)),
            "limit_distance_start": float(obj.get("spectra_limit_distance_start", 2.0)),
            "limit_distance_end": float(obj.get("spectra_limit_distance_end", 0.05)),
            "limit_frame_start": int(obj.get("spectra_limit_frame_start", 1)),
            "limit_frame_end": int(obj.get("spectra_limit_frame_end", 96)),
            "limit_estimate_tolerance": float(obj.get("spectra_limit_estimate_tolerance", 0.12)),
            "show_limit_guides": bool(obj.get("spectra_show_limit_guides", False)),
            "show_limit_hud": bool(obj.get("spectra_show_limit_hud", False)),
            "limit_hud_scale": float(obj.get("spectra_limit_hud_scale", 0.58)),
            "limit_show_hole": bool(obj.get("spectra_limit_show_hole", False)),
            "limit_hole_y": float(obj.get("spectra_limit_hole_y", 0.0)),
            "limit_show_target_point": bool(obj.get("spectra_limit_show_target_point", False)),
            "limit_target_point_y": float(obj.get("spectra_limit_target_point_y", 0.0)),
            "show_derivative_graph": bool(obj.get("spectra_show_derivative_graph", False)),
            "derivative_graph_offset_y": float(obj.get("spectra_derivative_graph_offset_y", -5.0)),
            "derivative_graph_scale_y": float(obj.get("spectra_derivative_graph_scale_y", 1.0)),
            "animate_secant_h": bool(obj.get("spectra_animate_secant_h", False)),
            "secant_h_start": float(obj.get("spectra_secant_h_start", 1.5)),
            "secant_h_end": float(obj.get("spectra_secant_h_end", 0.05)),
            "secant_frame_start": int(obj.get("spectra_secant_frame_start", 1)),
            "secant_frame_end": int(obj.get("spectra_secant_frame_end", 72)),
            "integral_a": float(obj.get("spectra_integral_a", -2.0)),
            "integral_b": float(obj.get("spectra_integral_b", 2.0)),
            "integral_samples": int(obj.get("spectra_integral_samples", 128)),
            "show_integral_area": bool(obj.get("spectra_show_integral_area", False)),
            "show_integral_bound_lines": bool(obj.get("spectra_show_integral_bound_lines", True)),
            "show_integral_bound_points": bool(obj.get("spectra_show_integral_bound_points", True)),
            "show_integral_hud": bool(obj.get("spectra_show_integral_hud", True)),
            "integral_hud_scale": float(obj.get("spectra_integral_hud_scale", 0.58)),
            "integral_scene_mode": obj.get("spectra_integral_scene_mode", "SIGNED_AREA"),
            "integral_value_mode": obj.get("spectra_integral_value_mode", "BOTH"),
            "integral_animation_mode": obj.get("spectra_integral_animation_mode", "NONE"),
            "integral_lower_start": float(obj.get("spectra_integral_lower_start", -2.0)),
            "integral_lower_end": float(obj.get("spectra_integral_lower_end", -1.0)),
            "integral_upper_start": float(obj.get("spectra_integral_upper_start", -2.0)),
            "integral_upper_end": float(obj.get("spectra_integral_upper_end", 2.0)),
            "integral_frame_start": int(obj.get("spectra_integral_frame_start", 1)),
            "integral_frame_end": int(obj.get("spectra_integral_frame_end", 96)),
            "integral_show_accumulation_graph": bool(obj.get("spectra_integral_show_accumulation_graph", False)),
            "integral_graph_offset_y": float(obj.get("spectra_integral_graph_offset_y", -7.0)),
            "integral_graph_scale_y": float(obj.get("spectra_integral_graph_scale_y", 1.0)),
            "integral_show_strip_preview": bool(obj.get("spectra_integral_show_strip_preview", False)),
            "integral_strip_count": int(obj.get("spectra_integral_strip_count", 12)),
            "title_text": obj.get("spectra_title_text", "Derivative Visualizer"),
        },
    )()


def sync_calculus_panel_from_object(obj, settings):
    settings.calculus_x = float(obj.get("spectra_calculus_x", settings.calculus_x))
    settings.calculus_h = float(obj.get("spectra_calculus_h", settings.calculus_h))
    settings.calculus_line_span = float(obj.get("spectra_calculus_line_span", settings.calculus_line_span))
    settings.show_moving_point = bool(obj.get("spectra_show_moving_point", settings.show_moving_point))
    settings.show_secant = bool(obj.get("spectra_show_secant", settings.show_secant))
    settings.show_tangent = bool(obj.get("spectra_show_tangent", settings.show_tangent))
    settings.show_area = bool(obj.get("spectra_show_area", settings.show_area))
    settings.area_x_min = float(obj.get("spectra_area_x_min", settings.area_x_min))
    settings.area_x_max = float(obj.get("spectra_area_x_max", settings.area_x_max))
    settings.area_samples = int(obj.get("spectra_area_samples", settings.area_samples))
    settings.animate_calculus_x = bool(obj.get("spectra_animate_calculus_x", settings.animate_calculus_x))
    settings.calculus_x_start = float(obj.get("spectra_calculus_x_start", settings.calculus_x_start))
    settings.calculus_x_end = float(obj.get("spectra_calculus_x_end", settings.calculus_x_end))
    settings.calculus_frame_start = int(obj.get("spectra_calculus_frame_start", settings.calculus_frame_start))
    settings.calculus_frame_end = int(obj.get("spectra_calculus_frame_end", settings.calculus_frame_end))
    settings.calculus_point_size = float(obj.get("spectra_calculus_point_size", settings.calculus_point_size))
    settings.derivative_show_hud = bool(obj.get("spectra_derivative_show_hud", settings.derivative_show_hud))
    settings.derivative_show_tangent_formula = bool(
        obj.get("spectra_derivative_show_tangent_formula", settings.derivative_show_tangent_formula)
    )
    settings.derivative_show_point_label = bool(
        obj.get("spectra_derivative_show_point_label", settings.derivative_show_point_label)
    )
    settings.derivative_show_angle_guide = bool(
        obj.get("spectra_derivative_show_angle_guide", settings.derivative_show_angle_guide)
    )
    settings.derivative_hud_scale = float(obj.get("spectra_derivative_hud_scale", settings.derivative_hud_scale))
    settings.limit_target_x = float(obj.get("spectra_limit_target_x", settings.limit_target_x))
    settings.limit_mode = obj.get("spectra_limit_mode", settings.limit_mode)
    settings.animate_limit = bool(obj.get("spectra_animate_limit", settings.animate_limit))
    settings.limit_distance_start = float(obj.get("spectra_limit_distance_start", settings.limit_distance_start))
    settings.limit_distance_end = float(obj.get("spectra_limit_distance_end", settings.limit_distance_end))
    settings.limit_frame_start = int(obj.get("spectra_limit_frame_start", settings.limit_frame_start))
    settings.limit_frame_end = int(obj.get("spectra_limit_frame_end", settings.limit_frame_end))
    settings.limit_estimate_tolerance = float(
        obj.get("spectra_limit_estimate_tolerance", settings.limit_estimate_tolerance)
    )
    settings.show_limit_guides = bool(obj.get("spectra_show_limit_guides", settings.show_limit_guides))
    settings.show_limit_hud = bool(obj.get("spectra_show_limit_hud", settings.show_limit_hud))
    settings.limit_hud_scale = float(obj.get("spectra_limit_hud_scale", settings.limit_hud_scale))
    settings.limit_show_hole = bool(obj.get("spectra_limit_show_hole", settings.limit_show_hole))
    settings.limit_hole_y = float(obj.get("spectra_limit_hole_y", settings.limit_hole_y))
    settings.limit_show_target_point = bool(
        obj.get("spectra_limit_show_target_point", settings.limit_show_target_point)
    )
    settings.limit_target_point_y = float(
        obj.get("spectra_limit_target_point_y", settings.limit_target_point_y)
    )
    settings.show_derivative_graph = bool(obj.get("spectra_show_derivative_graph", settings.show_derivative_graph))
    settings.derivative_graph_offset_y = float(
        obj.get("spectra_derivative_graph_offset_y", settings.derivative_graph_offset_y)
    )
    settings.derivative_graph_scale_y = float(
        obj.get("spectra_derivative_graph_scale_y", settings.derivative_graph_scale_y)
    )
    settings.animate_secant_h = bool(obj.get("spectra_animate_secant_h", settings.animate_secant_h))
    settings.secant_h_start = float(obj.get("spectra_secant_h_start", settings.secant_h_start))
    settings.secant_h_end = float(obj.get("spectra_secant_h_end", settings.secant_h_end))
    settings.secant_frame_start = int(obj.get("spectra_secant_frame_start", settings.secant_frame_start))
    settings.secant_frame_end = int(obj.get("spectra_secant_frame_end", settings.secant_frame_end))
    settings.integral_a = float(obj.get("spectra_integral_a", settings.integral_a))
    settings.integral_b = float(obj.get("spectra_integral_b", settings.integral_b))
    settings.integral_samples = int(obj.get("spectra_integral_samples", settings.integral_samples))
    settings.show_integral_area = bool(obj.get("spectra_show_integral_area", settings.show_integral_area))
    settings.show_integral_bound_lines = bool(
        obj.get("spectra_show_integral_bound_lines", settings.show_integral_bound_lines)
    )
    settings.show_integral_bound_points = bool(
        obj.get("spectra_show_integral_bound_points", settings.show_integral_bound_points)
    )
    settings.show_integral_hud = bool(obj.get("spectra_show_integral_hud", settings.show_integral_hud))
    settings.integral_hud_scale = float(obj.get("spectra_integral_hud_scale", settings.integral_hud_scale))
    settings.integral_scene_mode = obj.get("spectra_integral_scene_mode", settings.integral_scene_mode)
    settings.integral_value_mode = obj.get("spectra_integral_value_mode", settings.integral_value_mode)
    settings.integral_animation_mode = obj.get("spectra_integral_animation_mode", settings.integral_animation_mode)
    settings.integral_lower_start = float(obj.get("spectra_integral_lower_start", settings.integral_lower_start))
    settings.integral_lower_end = float(obj.get("spectra_integral_lower_end", settings.integral_lower_end))
    settings.integral_upper_start = float(obj.get("spectra_integral_upper_start", settings.integral_upper_start))
    settings.integral_upper_end = float(obj.get("spectra_integral_upper_end", settings.integral_upper_end))
    settings.integral_frame_start = int(obj.get("spectra_integral_frame_start", settings.integral_frame_start))
    settings.integral_frame_end = int(obj.get("spectra_integral_frame_end", settings.integral_frame_end))
    settings.integral_show_accumulation_graph = bool(
        obj.get("spectra_integral_show_accumulation_graph", settings.integral_show_accumulation_graph)
    )
    settings.integral_graph_offset_y = float(
        obj.get("spectra_integral_graph_offset_y", settings.integral_graph_offset_y)
    )
    settings.integral_graph_scale_y = float(
        obj.get("spectra_integral_graph_scale_y", settings.integral_graph_scale_y)
    )
    settings.integral_show_strip_preview = bool(
        obj.get("spectra_integral_show_strip_preview", settings.integral_show_strip_preview)
    )
    settings.integral_strip_count = int(obj.get("spectra_integral_strip_count", settings.integral_strip_count))


def _apply_integral_hud(context, graph_obj, graph_settings, panel_settings, a, b, signed_value, absolute_value):
    label_collection = _ensure_calculus_label_collection(context)
    roles = (
        "INTEGRAL_TITLE",
        "INTEGRAL_A",
        "INTEGRAL_B",
        "INTEGRAL_DELTA",
        "INTEGRAL_VALUE",
        "INTEGRAL_ABS",
        "INTEGRAL_SIGN",
    )
    if not panel_settings.show_integral_hud:
        for role in roles:
            obj = _find_child(label_collection, graph_obj.name, role)
            if obj:
                obj.hide_viewport = True
                obj.hide_render = True
        return
    for role, body, location, size in _integral_hud_items(
        graph_settings,
        panel_settings,
        a,
        b,
        signed_value,
        absolute_value,
    ):
        obj = _ensure_text_object(label_collection, graph_obj, role, size, location)
        obj.data.body = body
        obj.data.size = size
        obj.location = location
        obj.hide_viewport = False
        obj.hide_render = False


def _integral_strip_mesh_data(context, graph_settings, a, b, strip_count):
    mesh_data = {"verts": [], "faces": []}
    if a == b:
        return mesh_data
    lo, hi = (a, b) if a <= b else (b, a)
    dx = (hi - lo) / max(int(strip_count), 1)
    for index in range(max(int(strip_count), 1)):
        x_left = lo + dx * index
        x_right = x_left + dx
        sample_x = x_left + dx * 0.5
        y = safe_curve_value(context, graph_settings, sample_x)
        if y is None:
            continue
        _add_polygon(
            mesh_data,
            [(x_left, 0.0), (x_left, y), (x_right, y), (x_right, 0.0)],
            graph_settings,
        )
    return mesh_data


def _update_ftc_visuals(context, collection, graph_obj, graph_settings, panel_settings, a, b, sample_cache):
    if panel_settings.integral_scene_mode != "FTC":
        existing_curve = _find_child(collection, graph_obj.name, "INTEGRAL_FTC_TANGENT")
        existing_point = _find_child(collection, graph_obj.name, "INTEGRAL_FTC_POINT")
        if existing_curve:
            existing_curve.hide_viewport = True
            existing_curve.hide_render = True
        if existing_point:
            existing_point.hide_viewport = True
            existing_point.hide_render = True
        return existing_curve, existing_point

    ftc_curve = _ensure_integral_curve_object(
        collection,
        graph_obj,
        "INTEGRAL_FTC_TANGENT",
        (0.98, 0.55, 0.95, 1.0),
        thickness=0.014,
    )
    ftc_point = _ensure_integral_point_object(
        collection,
        graph_obj,
        "INTEGRAL_FTC_POINT",
        (0.98, 0.55, 0.95, 1.0),
    )
    x_value = clamp_x_value(graph_settings, b)
    accumulation_value = integrate_from_cache(sample_cache, a, x_value, absolute=False)
    world_point = Vector(
        math_to_world(
            graph_settings,
            x_value,
            accumulation_value * panel_settings.integral_graph_scale_y + panel_settings.integral_graph_offset_y,
            0.0,
        )
    )
    slope = safe_curve_value(context, graph_settings, x_value)
    if slope is None:
        ftc_curve.hide_viewport = True
        ftc_curve.hide_render = True
        ftc_point.hide_viewport = True
        ftc_point.hide_render = True
        return ftc_curve, ftc_point

    span = 1.35
    tangent_start = Vector(
        math_to_world(
            graph_settings,
            x_value - span,
            (accumulation_value - slope * span) * panel_settings.integral_graph_scale_y + panel_settings.integral_graph_offset_y,
            0.0,
        )
    )
    tangent_end = Vector(
        math_to_world(
            graph_settings,
            x_value + span,
            (accumulation_value + slope * span) * panel_settings.integral_graph_scale_y + panel_settings.integral_graph_offset_y,
            0.0,
        )
    )
    _set_line_points(ftc_curve, tangent_start, tangent_end)
    _apply_point_geometry(ftc_point, panel_settings.calculus_point_size * 0.6)
    ftc_point.location = world_point
    ftc_curve.hide_viewport = False
    ftc_curve.hide_render = False
    ftc_point.hide_viewport = False
    ftc_point.hide_render = False
    return ftc_curve, ftc_point


def _apply_limit_hud(context, graph_obj, graph_settings, panel_settings, x0, left_x, right_x, left_y, right_y, limit_text):
    label_collection = _ensure_calculus_label_collection(context)
    roles = ("LIMIT_TITLE", "LIMIT_TARGET", "LIMIT_LEFT", "LIMIT_RIGHT", "LIMIT_VALUE")
    if not panel_settings.show_limit_hud:
        for role in roles:
            obj = _find_child(label_collection, graph_obj.name, role)
            if obj:
                obj.hide_viewport = True
                obj.hide_render = True
        return
    for role, body, location, size in _limit_hud_items(
        graph_settings,
        panel_settings,
        x0,
        left_x,
        right_x,
        left_y,
        right_y,
        limit_text,
    ):
        obj = _ensure_text_object(label_collection, graph_obj, role, size, location)
        obj.data.body = body
        obj.data.size = size
        obj.location = location
        obj.hide_viewport = False
        obj.hide_render = False


def create_or_update_limit_visuals(context, graph_obj, panel_settings):
    if not is_spectra_object(graph_obj):
        raise FormulaValidationError("Select a Spectra curve graph first")
    graph_settings = settings_from_object(graph_obj)
    if graph_settings.graph_mode != "CURVE_2D":
        raise FormulaValidationError("Limit visuals currently work on 2D curve graphs only")

    collection = _ensure_calculus_collection(context)
    x0, left_x, right_x = _limit_positions(context, graph_settings, panel_settings)
    left_y = safe_curve_value(context, graph_settings, left_x)
    right_y = safe_curve_value(context, graph_settings, right_x)
    base_distance = max(_animated_limit_distance(context, panel_settings), 1e-5)
    left_estimate = _estimate_limit_side(context, graph_settings, x0, -1.0, base_distance)
    right_estimate = _estimate_limit_side(context, graph_settings, x0, 1.0, base_distance)
    limit_text = _describe_limit_value(
        left_estimate,
        right_estimate,
        panel_settings.limit_estimate_tolerance,
        panel_settings.limit_mode,
    )

    left_point = _ensure_limit_point_object(collection, graph_obj, "LIMIT_LEFT_POINT", (0.34, 0.82, 1.0, 1.0))
    right_point = _ensure_limit_point_object(collection, graph_obj, "LIMIT_RIGHT_POINT", (1.0, 0.72, 0.3, 1.0))
    target_point = _ensure_limit_point_object(collection, graph_obj, "LIMIT_TARGET_POINT", (1.0, 0.35, 0.35, 1.0))
    hole_point = _ensure_limit_point_object(collection, graph_obj, "LIMIT_HOLE_POINT", (0.95, 0.95, 0.95, 1.0))
    left_guide = _ensure_limit_curve_object(collection, graph_obj, "LIMIT_LEFT_GUIDE", (0.34, 0.82, 1.0, 1.0))
    right_guide = _ensure_limit_curve_object(collection, graph_obj, "LIMIT_RIGHT_GUIDE", (1.0, 0.72, 0.3, 1.0))

    _apply_point_geometry(left_point, panel_settings.calculus_point_size * 0.72)
    _apply_point_geometry(right_point, panel_settings.calculus_point_size * 0.72)
    _apply_point_geometry(target_point, panel_settings.calculus_point_size * 0.68)
    _apply_point_geometry(hole_point, panel_settings.calculus_point_size * 0.6)

    left_visible = panel_settings.limit_mode in {"TWO_SIDED", "LEFT_ONLY"} and left_y is not None
    right_visible = panel_settings.limit_mode in {"TWO_SIDED", "RIGHT_ONLY"} and right_y is not None

    if left_visible:
        left_curve = Vector(math_to_world(graph_settings, left_x, left_y, 0.0))
        left_axis = Vector(math_to_world(graph_settings, x0, 0.0, 0.0))
        left_point.location = left_curve
        _set_line_points(left_guide, left_axis, left_curve)
    if right_visible:
        right_curve = Vector(math_to_world(graph_settings, right_x, right_y, 0.0))
        right_axis = Vector(math_to_world(graph_settings, x0, 0.0, 0.0))
        right_point.location = right_curve
        _set_line_points(right_guide, right_axis, right_curve)

    hole_point.location = Vector(math_to_world(graph_settings, x0, panel_settings.limit_hole_y, 0.0))
    target_point.location = Vector(math_to_world(graph_settings, x0, panel_settings.limit_target_point_y, 0.0))

    left_point.hide_viewport = not left_visible
    left_point.hide_render = not left_visible
    right_point.hide_viewport = not right_visible
    right_point.hide_render = not right_visible
    left_guide.hide_viewport = not (panel_settings.show_limit_guides and left_visible)
    left_guide.hide_render = not (panel_settings.show_limit_guides and left_visible)
    right_guide.hide_viewport = not (panel_settings.show_limit_guides and right_visible)
    right_guide.hide_render = not (panel_settings.show_limit_guides and right_visible)
    hole_point.hide_viewport = not panel_settings.limit_show_hole
    hole_point.hide_render = not panel_settings.limit_show_hole
    target_point.hide_viewport = not panel_settings.limit_show_target_point
    target_point.hide_render = not panel_settings.limit_show_target_point

    _apply_limit_hud(context, graph_obj, graph_settings, panel_settings, x0, left_x, right_x, left_estimate, right_estimate, limit_text)
    update_calculus_metadata(graph_obj, panel_settings)
    _update_timeline_markers(context.scene, panel_settings)
    return [left_point, right_point, target_point, hole_point, left_guide, right_guide]


def _integral_mesh_data_for_bounds(context, graph_settings, a, b, sample_count):
    pos_data = {"verts": [], "faces": []}
    neg_data = {"verts": [], "faces": []}
    if a == b:
        return pos_data, neg_data
    steps = max(3, int(sample_count))
    lo, hi = (a, b) if a <= b else (b, a)
    dx = (hi - lo) / (steps - 1)
    prev_x = lo
    prev_y = safe_curve_value(context, graph_settings, prev_x)
    for index in range(1, steps):
        x = lo + dx * index
        y = safe_curve_value(context, graph_settings, x)
        if prev_y is None or y is None:
            prev_x = x
            prev_y = y
            continue
        _append_signed_segment(pos_data, neg_data, graph_settings, prev_x, prev_y, x, y)
        prev_x = x
        prev_y = y
    return pos_data, neg_data


def _update_accumulation_graph(context, collection, graph_obj, graph_settings, panel_settings, lower_bound, sample_cache):
    accumulation = _ensure_integral_curve_object(
        collection,
        graph_obj,
        "INTEGRAL_GRAPH",
        (0.95, 0.9, 0.3, 1.0),
        thickness=0.016,
    )
    if not (panel_settings.integral_show_accumulation_graph or panel_settings.integral_scene_mode in {"ACCUMULATION", "FTC"}):
        accumulation.hide_viewport = True
        accumulation.hide_render = True
        return accumulation
    step_count = max(16, min(graph_settings.samples, 512))
    span = graph_settings.x_max - graph_settings.x_min
    points = []
    for index in range(step_count):
        factor = index / (step_count - 1)
        x_value = graph_settings.x_min + span * factor
        integral_value = integrate_from_cache(sample_cache, lower_bound, x_value, absolute=False)
        points.append(
            math_to_world(
                graph_settings,
                x_value,
                integral_value * panel_settings.integral_graph_scale_y + panel_settings.integral_graph_offset_y,
                0.0,
            )
        )
    _apply_curve_points(accumulation.data, points)
    accumulation.hide_viewport = False
    accumulation.hide_render = False
    return accumulation


def create_or_update_integral_visuals(context, graph_obj, panel_settings):
    if not is_spectra_object(graph_obj):
        raise FormulaValidationError("Select a Spectra curve graph first")
    graph_settings = settings_from_object(graph_obj)
    if graph_settings.graph_mode != "CURVE_2D":
        raise FormulaValidationError("Integral visuals currently work on 2D curve graphs only")

    a_raw, b_raw = integral_bounds(context, panel_settings)
    a, b = clamp_bound_pair(graph_settings, a_raw, b_raw)
    cache_steps = max(panel_settings.integral_samples, graph_settings.samples, panel_settings.integral_strip_count * 2)
    sample_cache = build_curve_sample_cache(context, graph_settings, cache_steps)
    integral_value = integrate_from_cache(sample_cache, a, b, absolute=False)
    absolute_value = integrate_from_cache(sample_cache, a, b, absolute=True)
    pos_data, neg_data = _integral_mesh_data_for_bounds(context, graph_settings, a, b, panel_settings.integral_samples)
    strip_data = _integral_strip_mesh_data(context, graph_settings, a, b, panel_settings.integral_strip_count)

    collection = _ensure_calculus_collection(context)
    positive = _ensure_integral_mesh_object(collection, graph_obj, "INTEGRAL_POS_AREA", (0.2, 0.9, 0.5, 0.4))
    negative = _ensure_integral_mesh_object(collection, graph_obj, "INTEGRAL_NEG_AREA", (1.0, 0.32, 0.32, 0.4))
    strips = _ensure_integral_mesh_object(collection, graph_obj, "INTEGRAL_STRIPS", (0.8, 0.88, 1.0, 0.22))
    _apply_mesh_data(positive, pos_data)
    _apply_mesh_data(negative, neg_data)
    _apply_mesh_data(strips, strip_data)

    a_world = Vector(math_to_world(graph_settings, a, 0.0, 0.0))
    b_world = Vector(math_to_world(graph_settings, b, 0.0, 0.0))
    a_curve = curve_point(context, graph_settings, a)
    b_curve = curve_point(context, graph_settings, b)

    left_bound = _ensure_integral_curve_object(collection, graph_obj, "INTEGRAL_LEFT_BOUND", (0.95, 0.95, 0.95, 1.0), thickness=0.015)
    right_bound = _ensure_integral_curve_object(collection, graph_obj, "INTEGRAL_RIGHT_BOUND", (0.95, 0.95, 0.95, 1.0), thickness=0.015)
    _set_line_points(left_bound, a_world, a_curve)
    _set_line_points(right_bound, b_world, b_curve)

    left_point = _ensure_integral_point_object(collection, graph_obj, "INTEGRAL_LEFT_POINT", (0.95, 0.95, 0.95, 1.0))
    right_point = _ensure_integral_point_object(collection, graph_obj, "INTEGRAL_RIGHT_POINT", (0.95, 0.95, 0.95, 1.0))
    _apply_point_geometry(left_point, panel_settings.calculus_point_size * 0.7)
    _apply_point_geometry(right_point, panel_settings.calculus_point_size * 0.7)
    left_point.location = a_curve
    right_point.location = b_curve

    accumulation = _update_accumulation_graph(context, collection, graph_obj, graph_settings, panel_settings, a, sample_cache)
    ftc_curve, ftc_point = _update_ftc_visuals(context, collection, graph_obj, graph_settings, panel_settings, a, b, sample_cache)

    show_area_meshes = panel_settings.show_integral_area
    show_accumulation = panel_settings.integral_scene_mode in {"ACCUMULATION", "FTC"} or panel_settings.integral_show_accumulation_graph
    positive.hide_viewport = not show_area_meshes
    positive.hide_render = not show_area_meshes
    negative.hide_viewport = not show_area_meshes
    negative.hide_render = not show_area_meshes
    strips.hide_viewport = not panel_settings.integral_show_strip_preview
    strips.hide_render = not panel_settings.integral_show_strip_preview
    left_bound.hide_viewport = not panel_settings.show_integral_bound_lines
    left_bound.hide_render = not panel_settings.show_integral_bound_lines
    right_bound.hide_viewport = not panel_settings.show_integral_bound_lines
    right_bound.hide_render = not panel_settings.show_integral_bound_lines
    left_point.hide_viewport = not panel_settings.show_integral_bound_points
    left_point.hide_render = not panel_settings.show_integral_bound_points
    right_point.hide_viewport = not panel_settings.show_integral_bound_points
    right_point.hide_render = not panel_settings.show_integral_bound_points
    accumulation.hide_viewport = not show_accumulation
    accumulation.hide_render = not show_accumulation

    _apply_integral_hud(context, graph_obj, graph_settings, panel_settings, a, b, integral_value, absolute_value)
    update_calculus_metadata(graph_obj, panel_settings)
    _update_timeline_markers(context.scene, panel_settings)
    return [positive, negative, strips, left_bound, right_bound, left_point, right_point, accumulation, ftc_curve, ftc_point]


def refresh_calculus_for_graph(context, graph_obj):
    settings = calculus_settings_from_object(graph_obj)
    if graph_obj.get("spectra_calculus_enabled"):
        create_or_update_calculus_visuals(context, graph_obj, settings)
    if graph_obj.get("spectra_limit_enabled"):
        create_or_update_limit_visuals(context, graph_obj, settings)
    if graph_obj.get("spectra_integral_enabled"):
        create_or_update_integral_visuals(context, graph_obj, settings)
