import bpy
from mathutils import Euler

from .math_parser import resolve_parameter_scope


SPECTRA_AUX_COLLECTIONS = (
    "Spectra Calculus",
    "Spectra Calculus Labels",
    "Spectra Labels",
)


def ensure_material(name, color):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name=name)
        material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.35
    return material


def clear_collection_objects(collection):
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def ensure_guide_collection(context, name="Spectra Guides"):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(collection)
    return collection


def ensure_text_material():
    return ensure_material("SpectraTextMaterial", (0.98, 0.98, 1.0, 1.0))


def ensure_grid_material(name, color):
    material = ensure_material(name, color)
    if hasattr(material, "blend_method"):
        material.blend_method = "BLEND"
    return material


def clear_default_scene(context):
    for name in ("Cube", "Light", "Camera"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def purge_spectra_graphs(context, collection_name="Spectra Graphs"):
    graph_collection = bpy.data.collections.get(collection_name)
    graph_names = []
    if graph_collection is not None:
        graph_names = [obj.name for obj in graph_collection.objects]
        clear_collection_objects(graph_collection)

    for aux_name in SPECTRA_AUX_COLLECTIONS:
        aux_collection = bpy.data.collections.get(aux_name)
        if aux_collection is None:
            continue
        for obj in list(aux_collection.objects):
            graph_name = obj.get("spectra_calculus_graph")
            if not graph_names or graph_name in graph_names or obj.name.startswith("Spectra"):
                bpy.data.objects.remove(obj, do_unlink=True)


def purge_all_spectra_helpers():
    for aux_name in SPECTRA_AUX_COLLECTIONS:
        aux_collection = bpy.data.collections.get(aux_name)
        clear_collection_objects(aux_collection)


def purge_spectra_timeline_markers(scene):
    for marker in list(scene.timeline_markers):
        if marker.name.startswith("Spectra "):
            scene.timeline_markers.remove(marker)


def ensure_camera(context, mode):
    camera = bpy.data.objects.get("SpectraCamera")
    if camera is None:
        camera_data = bpy.data.cameras.new("SpectraCamera")
        camera = bpy.data.objects.new("SpectraCamera", camera_data)
        context.scene.collection.objects.link(camera)

    if mode == "MODE_2D":
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = 20.0
        camera.location = (0.0, 0.0, 18.0)
        camera.rotation_euler = Euler((0.0, 0.0, 0.0))
    else:
        camera.data.type = "PERSP"
        camera.location = (12.0, -14.0, 10.0)
        camera.rotation_euler = Euler((1.0, 0.0, 0.7))

    context.scene.camera = camera
    return camera


def ensure_light(context, mode):
    light = bpy.data.objects.get("SpectraLight")
    if light is None:
        light_data = bpy.data.lights.new("SpectraLight", type="SUN")
        light = bpy.data.objects.new("SpectraLight", light_data)
        context.scene.collection.objects.link(light)
    light.location = (7.0, -8.0, 14.0) if mode == "MODE_3D" else (0.0, 0.0, 12.0)
    light.rotation_euler = Euler((0.75, 0.0, 0.55)) if mode == "MODE_3D" else Euler((0.0, 0.0, 0.0))
    light.data.energy = 3.8

    fill = bpy.data.objects.get("SpectraFill")
    if fill is None:
        fill_data = bpy.data.lights.new("SpectraFill", type="AREA")
        fill = bpy.data.objects.new("SpectraFill", fill_data)
        context.scene.collection.objects.link(fill)
    fill.location = (0.0, -6.5, 8.5) if mode == "MODE_3D" else (0.0, 0.0, 9.5)
    fill.rotation_euler = Euler((1.5708, 0.0, 0.0))
    fill.data.energy = 700.0 if mode == "MODE_3D" else 450.0
    fill.data.shape = "RECTANGLE"
    fill.data.size = 14.0
    fill.data.size_y = 8.0
    return light


def ensure_world(context):
    world = context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
        background.inputs[1].default_value = 0.42
    return world


def _create_line_object(name, start, end, thickness, material):
    curve = bpy.data.curves.new(name=name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 4
    curve.bevel_depth = thickness
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (*start, 1.0)
    spline.points[1].co = (*end, 1.0)
    curve.materials.append(material)
    return bpy.data.objects.new(name, curve)


def _link_guide_object(collection, scene_collection, obj):
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)
    if scene_collection.objects.get(obj.name):
        scene_collection.objects.unlink(obj)


def _create_grid_and_ticks(context, settings, collection, extent=10, step=1.0):
    minor_material = ensure_grid_material("SpectraGridMinorMaterial", (0.23, 0.23, 0.23, 0.55))
    major_material = ensure_grid_material("SpectraGridMajorMaterial", (0.42, 0.42, 0.42, 0.7))
    axis_x_material = ensure_material("SpectraXAxisMaterial", (1.0, 0.38, 0.38, 1.0))
    axis_y_material = ensure_material("SpectraYAxisMaterial", (0.35, 1.0, 0.52, 1.0))

    for index in range(-extent, extent + 1):
        if index == 0:
            continue
        if getattr(settings, "coordinate_show_grid", True):
            material = major_material if index % 2 == 0 else minor_material
            thickness = 0.012 if index % 2 == 0 else 0.006

            vertical = _create_line_object(
                f"SpectraGridX{index}",
                (index * step, -extent * step, 0.0),
                (index * step, extent * step, 0.0),
                thickness,
                material,
            )
            horizontal = _create_line_object(
                f"SpectraGridY{index}",
                (-extent * step, index * step, 0.0),
                (extent * step, index * step, 0.0),
                thickness,
                material,
            )
            _link_guide_object(collection, context.scene.collection, vertical)
            _link_guide_object(collection, context.scene.collection, horizontal)

        tick_x = _create_line_object(
            f"SpectraTickX{index}",
            (index * step, -0.18, 0.0),
            (index * step, 0.18, 0.0),
            0.01,
            axis_x_material,
        )
        tick_y = _create_line_object(
            f"SpectraTickY{index}",
            (-0.18, index * step, 0.0),
            (0.18, index * step, 0.0),
            0.01,
            axis_y_material,
        )
        _link_guide_object(collection, context.scene.collection, tick_x)
        _link_guide_object(collection, context.scene.collection, tick_y)

        if getattr(settings, "coordinate_show_tick_labels", True):
            label_size = 0.28
            label_value = index * getattr(settings, "coordinate_step", 1.0)
            label_text = f"{label_value:g}"
            x_text = _create_text_object(
                f"SpectraTickLabelX{index}",
                label_text,
                label_size,
                (index * step - 0.12, -0.52, 0.0),
                align_x="CENTER",
            )
            y_text = _create_text_object(
                f"SpectraTickLabelY{index}",
                label_text,
                label_size,
                (-0.42, index * step - 0.03, 0.0),
                align_x="RIGHT",
            )
            _link_guide_object(collection, context.scene.collection, x_text)
            _link_guide_object(collection, context.scene.collection, y_text)


def _create_2d_axes(context, settings, collection, extent=10, step=1.0):
    _create_grid_and_ticks(context, settings, collection, extent=extent, step=step)
    x_axis = _create_line_object(
        "X Axis",
        (-extent * step, 0.0, 0.0),
        (extent * step, 0.0, 0.0),
        0.028,
        ensure_material("SpectraXAxisMaterial", (1.0, 0.38, 0.38, 1.0)),
    )
    y_axis = _create_line_object(
        "Y Axis",
        (0.0, -extent * step, 0.0),
        (0.0, extent * step, 0.0),
        0.028,
        ensure_material("SpectraYAxisMaterial", (0.35, 1.0, 0.52, 1.0)),
    )
    _link_guide_object(collection, context.scene.collection, x_axis)
    _link_guide_object(collection, context.scene.collection, y_axis)

    x_label = _create_text_object("SpectraAxisLabelX", "x", 0.42, (extent * step + 0.45, -0.38, 0.0))
    y_label = _create_text_object("SpectraAxisLabelY", "y", 0.42, (-0.36, extent * step + 0.45, 0.0))
    _link_guide_object(collection, context.scene.collection, x_label)
    _link_guide_object(collection, context.scene.collection, y_label)


def _create_3d_axes(context, collection, length=10.0):
    axis_specs = [
        ("X Axis", (-length, 0.0, 0.0), (length, 0.0, 0.0), 0.028, (1.0, 0.38, 0.38, 1.0)),
        ("Y Axis", (0.0, -length, 0.0), (0.0, length, 0.0), 0.028, (0.35, 1.0, 0.52, 1.0)),
        ("Z Axis", (0.0, 0.0, -length * 0.2), (0.0, 0.0, length), 0.028, (0.35, 0.6, 1.0, 1.0)),
    ]
    for name, start, end, thickness, color in axis_specs:
        axis = _create_line_object(name, start, end, thickness, ensure_material(f"{name}Material", color))
        _link_guide_object(collection, context.scene.collection, axis)


def create_axes(context, settings):
    collection = ensure_guide_collection(context)

    clear_collection_objects(collection)
    extent = max(int(getattr(settings, "coordinate_extent", 10)), 2)
    step = max(float(getattr(settings, "coordinate_step", 1.0)), 0.0001)
    scale = max(float(getattr(settings, "coordinate_unit_scale", 1.0)), 0.0001)
    if settings.scene_mode == "MODE_2D":
        _create_2d_axes(context, settings, collection, extent=extent, step=step * scale)
    else:
        _create_3d_axes(context, collection, length=extent * step * scale)


def clear_labels(context):
    collection = ensure_guide_collection(context, "Spectra Labels")
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _create_text_object(name, body, size, location, rotation=(0.0, 0.0, 0.0), align_x="LEFT"):
    curve = bpy.data.curves.new(name=name, type="FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align_x
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler = Euler(rotation)
    curve.materials.append(ensure_text_material())
    return obj


def create_labels(context, settings):
    clear_labels(context)
    collection = ensure_guide_collection(context, "Spectra Labels")

    inferred_prefix = "y =" if settings.graph_mode == "CURVE_2D" else "z ="
    formula_body = settings.formula_label.strip() or f"{inferred_prefix} {settings.expression}"
    parameter_scope = resolve_parameter_scope(context.scene.frame_current, settings)
    parameter_text = ", ".join(
        f"{name}={value:.3f}" for name, value in sorted(parameter_scope.items())
    )
    if settings.scene_mode == "MODE_2D":
        title = _create_text_object(
            "SpectraTitle",
            settings.title_text,
            settings.label_size,
            (-8.7, 7.7, 0.0),
        )
        formula = _create_text_object(
            "SpectraFormula",
            formula_body,
            settings.label_size * 0.82,
            (-8.7, 6.65, 0.0),
        )
        parameter_label = _create_text_object(
            "SpectraParams",
            parameter_text or "Parameters: none",
            settings.label_size * 0.58,
            (-8.7, 5.8, 0.0),
        )
        labels = (title, formula, parameter_label)
    else:
        title = _create_text_object(
            "SpectraTitle",
            settings.title_text,
            settings.label_size,
            (-7.0, -8.0, 8.5),
            rotation=(1.15, 0.0, 0.3),
        )
        formula = _create_text_object(
            "SpectraFormula",
            formula_body,
            settings.label_size * 0.82,
            (-7.0, -8.0, 7.2),
            rotation=(1.15, 0.0, 0.3),
        )
        parameter_label = _create_text_object(
            "SpectraParams",
            parameter_text or "Parameters: none",
            settings.label_size * 0.58,
            (-7.0, -8.0, 6.15),
            rotation=(1.15, 0.0, 0.3),
        )
        labels = (title, formula, parameter_label)

    for label in labels:
        if collection.objects.get(label.name) is None:
            collection.objects.link(label)


def animate_graph(obj, settings):
    start = settings.animation_start
    end = start + settings.animation_duration

    obj.animation_data_clear()
    if obj.type == "CURVE":
        obj.data.animation_data_clear()

    if obj.type == "CURVE":
        if settings.animation_style == "RISE":
            obj.scale = (1.0, 0.01, 1.0)
            obj.keyframe_insert(data_path="scale", frame=start)
            obj.scale = (1.0, 1.0, 1.0)
            obj.keyframe_insert(data_path="scale", frame=end)
        else:
            obj.data.bevel_factor_mapping_start = "SPLINE"
            obj.data.bevel_factor_mapping_end = "SPLINE"
            obj.data.bevel_factor_end = 0.0
            obj.data.keyframe_insert(data_path="bevel_factor_end", frame=start)
            obj.data.bevel_factor_end = 1.0
            obj.data.keyframe_insert(data_path="bevel_factor_end", frame=end)
    else:
        if settings.animation_style == "DRAW":
            obj.scale = (1.0, 1.0, 0.001)
            obj.keyframe_insert(data_path="scale", frame=start)
            obj.scale = (1.0, 1.0, 1.0)
            obj.keyframe_insert(data_path="scale", frame=end)
        else:
            obj.location.z -= 2.0
            obj.keyframe_insert(data_path="location", frame=start)
            obj.location.z += 2.0
            obj.keyframe_insert(data_path="location", frame=end)

    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "BEZIER"


def setup_scene(context, settings):
    clear_default_scene(context)
    purge_all_spectra_helpers()
    purge_spectra_timeline_markers(context.scene)
    ensure_world(context)
    ensure_camera(context, settings.scene_mode)
    ensure_light(context, settings.scene_mode)
    create_axes(context, settings)

    context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    context.scene.eevee.use_gtao = True
    context.scene.eevee.taa_samples = 32
    if hasattr(context.scene.eevee, "use_bloom"):
        context.scene.eevee.use_bloom = True
    if hasattr(context.scene.eevee, "bloom_intensity"):
        context.scene.eevee.bloom_intensity = 0.03
    context.scene.render.resolution_x = 1920
    context.scene.render.resolution_y = 1080
    context.scene.render.film_transparent = False
    context.scene.view_settings.look = "AgX - Medium High Contrast"
    if settings.scene_mode == "MODE_2D":
        context.scene.camera.data.ortho_scale = (
            max(int(getattr(settings, "coordinate_extent", 10)), 2)
            * max(float(getattr(settings, "coordinate_step", 1.0)), 0.0001)
            * max(float(getattr(settings, "coordinate_unit_scale", 1.0)), 0.0001)
            * 2.4
        )
    context.scene.frame_start = 1
    context.scene.frame_end = 180
    context.scene.frame_current = 1
