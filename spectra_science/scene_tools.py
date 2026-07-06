import bpy
from mathutils import Euler

from .math_parser import resolve_parameter_scope


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


def ensure_guide_collection(context, name="Spectra Guides"):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(collection)
    return collection


def ensure_text_material():
    return ensure_material("SpectraTextMaterial", (0.98, 0.98, 1.0, 1.0))


def clear_default_scene(context):
    for name in ("Cube", "Light", "Camera"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


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
    light.location = (6.0, -6.0, 12.0) if mode == "MODE_3D" else (0.0, 0.0, 10.0)
    light.data.energy = 3.0
    return light


def ensure_world(context):
    world = context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs[0].default_value = (0.012, 0.014, 0.02, 1.0)
        background.inputs[1].default_value = 0.85
    return world


def create_axes(context, mode, length=10.0):
    collection = ensure_guide_collection(context)

    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    axis_specs = [
        ("X Axis", (length, 0.02, 0.02), (1.0, 0.25, 0.25, 1.0), (length / 2.0, 0.0, 0.0)),
        ("Y Axis", (0.02, length, 0.02), (0.25, 1.0, 0.4, 1.0), (0.0, length / 2.0, 0.0)),
    ]

    if mode == "MODE_3D":
        axis_specs.append(
            ("Z Axis", (0.02, 0.02, length), (0.3, 0.55, 1.0, 1.0), (0.0, 0.0, length / 2.0))
        )

    for name, scale, color, location in axis_specs:
        bpy.ops.mesh.primitive_cube_add(location=location)
        axis = context.active_object
        axis.name = name
        axis.scale = scale
        material = ensure_material(f"{name}Material", color)
        axis.data.materials.clear()
        axis.data.materials.append(material)
        if collection.objects.get(axis.name) is None:
            collection.objects.link(axis)
        if context.scene.collection.objects.get(axis.name):
            context.scene.collection.objects.unlink(axis)


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
        x_label = _create_text_object("SpectraXLabel", "x", settings.label_size * 0.8, (10.5, -0.4, 0.0))
        y_label = _create_text_object("SpectraYLabel", "y", settings.label_size * 0.8, (-0.45, 10.5, 0.0))
        labels = (title, formula, parameter_label, x_label, y_label)
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
        x_label = _create_text_object("SpectraXLabel", "x", settings.label_size * 0.8, (10.4, 0.0, 0.0))
        y_label = _create_text_object("SpectraYLabel", "y", settings.label_size * 0.8, (0.0, 10.4, 0.0))
        z_label = _create_text_object("SpectraZLabel", "z", settings.label_size * 0.8, (0.0, 0.0, 10.4))
        labels = (title, formula, parameter_label, x_label, y_label, z_label)

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


def setup_scene(context, mode):
    clear_default_scene(context)
    ensure_world(context)
    ensure_camera(context, mode)
    ensure_light(context, mode)
    create_axes(context, mode)

    context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    context.scene.frame_start = 1
    context.scene.frame_end = 180
    context.scene.frame_current = 1
