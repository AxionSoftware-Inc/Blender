import bpy

from .calculus_tools import (
    create_or_update_calculus_visuals,
    create_or_update_integral_visuals,
    create_or_update_limit_visuals,
    sync_calculus_panel_from_object,
)
from .graph_builders import (
    build_curve_graph,
    is_spectra_curve_object,
    is_spectra_object,
    build_surface_graph,
    update_graph_object,
)
from .math_parser import FormulaValidationError
from .scene_tools import (
    animate_graph,
    create_labels,
    purge_spectra_graphs,
    purge_spectra_timeline_markers,
    setup_scene,
)
from .templates import apply_derivative_template, apply_integral_template, apply_limit_template


def _select_only(context, obj):
    for selected in list(context.selected_objects):
        selected.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj


def _build_graph_from_settings(context, settings):
    if settings.graph_mode == "CURVE_2D":
        return build_curve_graph(context, settings)
    return build_surface_graph(context, settings)


def _apply_template_and_build(context, template_kind):
    settings = context.scene.spectra_settings
    if template_kind == "DERIVATIVE":
        apply_derivative_template(settings, context.scene)
    elif template_kind == "LIMIT":
        apply_limit_template(settings, context.scene)
    elif template_kind == "INTEGRAL":
        apply_integral_template(settings, context.scene)
    else:
        raise FormulaValidationError(f"Unknown template: {template_kind}")

    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end

    purge_spectra_graphs(context, settings.collection_name)
    setup_scene(context, settings)
    purge_spectra_timeline_markers(context.scene)
    context.scene.frame_start = frame_start
    context.scene.frame_end = frame_end
    context.scene.frame_current = frame_start

    graph_obj = None
    try:
        graph_obj = _build_graph_from_settings(context, settings)
        _select_only(context, graph_obj)

        if settings.animate_on_create:
            animate_graph(graph_obj, settings)
        if settings.show_labels:
            create_labels(context, settings)

        if template_kind == "LIMIT" and graph_obj.get("spectra_mode") == "CURVE_2D":
            create_or_update_limit_visuals(context, graph_obj, settings)
        elif template_kind == "DERIVATIVE" and graph_obj.get("spectra_mode") == "CURVE_2D":
            create_or_update_calculus_visuals(context, graph_obj, settings)
        elif template_kind == "INTEGRAL" and graph_obj.get("spectra_mode") == "CURVE_2D":
            create_or_update_integral_visuals(context, graph_obj, settings)

        context.scene.frame_set(frame_start)
        _select_only(context, graph_obj)
        return graph_obj
    except Exception:
        purge_spectra_graphs(context, settings.collection_name)
        purge_spectra_timeline_markers(context.scene)
        raise


class SPECTRA_OT_setup_scene(bpy.types.Operator):
    bl_idname = "spectra.setup_scene"
    bl_label = "Setup Scientific Scene"
    bl_description = "Prepare a clean 2D or 3D scene for scientific work"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.spectra_settings
        setup_scene(context, settings)
        self.report({"INFO"}, f"Scene prepared in {settings.scene_mode[-2:]} mode")
        return {"FINISHED"}


class SPECTRA_OT_generate_graph(bpy.types.Operator):
    bl_idname = "spectra.generate_graph"
    bl_label = "Generate Graph"
    bl_description = "Create a graph object from the current formula"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.spectra_settings
        if settings.graph_mode == "SURFACE_3D" and settings.scene_mode == "MODE_2D":
            settings.scene_mode = "MODE_3D"
            self.report({"INFO"}, "Switched scene mode to 3D for surface graph generation")
        purge_spectra_graphs(context, settings.collection_name)
        try:
            if settings.graph_mode == "CURVE_2D":
                obj = build_curve_graph(context, settings)
            else:
                obj = build_surface_graph(context, settings)
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Graph generation failed: {exc}")
            return {"CANCELLED"}

        context.view_layer.objects.active = obj
        obj.select_set(True)
        if settings.animate_on_create:
            animate_graph(obj, settings)
        if settings.show_labels:
            create_labels(context, settings)
        self.report({"INFO"}, f"Created {obj.name}")
        return {"FINISHED"}


class SPECTRA_OT_update_graph(bpy.types.Operator):
    bl_idname = "spectra.update_graph"
    bl_label = "Update Selected"
    bl_description = "Rebuild the selected Spectra graph from the current panel settings"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_spectra_object(context.active_object)

    def execute(self, context):
        settings = context.scene.spectra_settings
        obj = context.active_object
        if settings.graph_mode == "SURFACE_3D" and settings.scene_mode == "MODE_2D":
            settings.scene_mode = "MODE_3D"
        try:
            update_graph_object(context, obj, settings)
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Graph update failed: {exc}")
            return {"CANCELLED"}

        if settings.animate_on_create:
            animate_graph(obj, settings)
        if settings.show_labels:
            create_labels(context, settings)
        if obj.get("spectra_limit_enabled"):
            create_or_update_limit_visuals(context, obj, settings)
        if obj.get("spectra_integral_enabled"):
            create_or_update_integral_visuals(context, obj, settings)
        if obj.get("spectra_calculus_enabled"):
            create_or_update_calculus_visuals(context, obj, settings)
        self.report({"INFO"}, f"Updated {obj.name}")
        return {"FINISHED"}


class SPECTRA_OT_clear_graphs(bpy.types.Operator):
    bl_idname = "spectra.clear_graphs"
    bl_label = "Clear Graphs"
    bl_description = "Remove generated Spectra graph objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        purge_spectra_graphs(context, context.scene.spectra_settings.collection_name)
        self.report({"INFO"}, "Cleared graph objects")
        return {"FINISHED"}


class SPECTRA_OT_create_labels(bpy.types.Operator):
    bl_idname = "spectra.create_labels"
    bl_label = "Create Labels"
    bl_description = "Create scene labels for title, formula and axes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        create_labels(context, context.scene.spectra_settings)
        self.report({"INFO"}, "Labels created")
        return {"FINISHED"}


class SPECTRA_OT_sync_selected_to_panel(bpy.types.Operator):
    bl_idname = "spectra.sync_selected_to_panel"
    bl_label = "Load Selected Settings"
    bl_description = "Copy the active Spectra object's settings into the panel"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_spectra_object(context.active_object)

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.spectra_settings
        settings.expression = obj.get("spectra_formula", settings.expression)
        settings.active_template = obj.get("spectra_active_template", settings.active_template)
        settings.graph_mode = obj.get("spectra_mode", settings.graph_mode)
        settings.scene_mode = obj.get("spectra_scene_mode", settings.scene_mode)
        settings.collection_name = obj.get("spectra_collection_name", settings.collection_name)
        settings.coordinate_extent = int(obj.get("spectra_coordinate_extent", settings.coordinate_extent))
        settings.coordinate_step = float(obj.get("spectra_coordinate_step", settings.coordinate_step))
        settings.coordinate_unit_scale = float(obj.get("spectra_coordinate_unit_scale", settings.coordinate_unit_scale))
        settings.coordinate_show_grid = bool(obj.get("spectra_coordinate_show_grid", settings.coordinate_show_grid))
        settings.coordinate_show_tick_labels = bool(
            obj.get("spectra_coordinate_show_tick_labels", settings.coordinate_show_tick_labels)
        )
        settings.x_min = float(obj.get("spectra_x_min", settings.x_min))
        settings.x_max = float(obj.get("spectra_x_max", settings.x_max))
        settings.y_min = float(obj.get("spectra_y_min", settings.y_min))
        settings.y_max = float(obj.get("spectra_y_max", settings.y_max))
        settings.samples = int(obj.get("spectra_samples", settings.samples))
        settings.samples_x = int(obj.get("spectra_samples_x", settings.samples_x))
        settings.samples_y = int(obj.get("spectra_samples_y", settings.samples_y))
        settings.curve_thickness = float(obj.get("spectra_curve_thickness", settings.curve_thickness))
        settings.frame_rate_hint = float(obj.get("spectra_frame_rate_hint", settings.frame_rate_hint))
        settings.parameter_values = obj.get("spectra_parameter_values", settings.parameter_values)
        settings.live_formula_animation = bool(obj.get("spectra_live_formula_animation", settings.live_formula_animation))
        settings.parameter_animation_enabled = bool(
            obj.get("spectra_parameter_animation_enabled", settings.parameter_animation_enabled)
        )
        settings.animated_parameter = obj.get("spectra_animated_parameter", settings.animated_parameter)
        settings.animated_parameter_start = float(
            obj.get("spectra_animated_parameter_start", settings.animated_parameter_start)
        )
        settings.animated_parameter_end = float(
            obj.get("spectra_animated_parameter_end", settings.animated_parameter_end)
        )
        settings.parameter_frame_start = int(obj.get("spectra_parameter_frame_start", settings.parameter_frame_start))
        settings.parameter_frame_end = int(obj.get("spectra_parameter_frame_end", settings.parameter_frame_end))
        settings.title_text = obj.get("spectra_title_text", settings.title_text)
        settings.formula_label = obj.get("spectra_formula_label", settings.formula_label)
        settings.label_size = float(obj.get("spectra_label_size", settings.label_size))
        settings.show_labels = bool(obj.get("spectra_show_labels", settings.show_labels))
        sync_calculus_panel_from_object(obj, settings)
        self.report({"INFO"}, "Loaded selected Spectra settings into the panel")
        return {"FINISHED"}


class SPECTRA_OT_create_calculus_visuals(bpy.types.Operator):
    bl_idname = "spectra.create_calculus_visuals"
    bl_label = "Create Calculus Visuals"
    bl_description = "Build moving point, secant, tangent and area visuals for the selected curve"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_spectra_curve_object(context.active_object)

    def execute(self, context):
        settings = context.scene.spectra_settings
        obj = context.active_object
        if obj.get("spectra_mode") != "CURVE_2D":
            self.report({"ERROR"}, "Calculus visuals require a 2D curve graph")
            return {"CANCELLED"}
        try:
            create_or_update_calculus_visuals(context, obj, settings)
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Calculus build failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, "Calculus visuals created")
        return {"FINISHED"}


class SPECTRA_OT_create_limit_visuals(bpy.types.Operator):
    bl_idname = "spectra.create_limit_visuals"
    bl_label = "Create Limit Visuals"
    bl_description = "Build animated approach points, guides and HUD for the selected curve"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_spectra_curve_object(context.active_object)

    def execute(self, context):
        settings = context.scene.spectra_settings
        obj = context.active_object
        try:
            create_or_update_limit_visuals(context, obj, settings)
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Limit build failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, "Limit visuals created")
        return {"FINISHED"}


class SPECTRA_OT_apply_limit_template(bpy.types.Operator):
    bl_idname = "spectra.apply_limit_template"
    bl_label = "Build Limit Template"
    bl_description = "Build a complete limit teaching scene with graph, approach guides, labels, HUD and timeline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            obj = _apply_template_and_build(context, "LIMIT")
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Limit template build failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built limit template on {obj.name}")
        return {"FINISHED"}


class SPECTRA_OT_apply_derivative_preset(bpy.types.Operator):
    bl_idname = "spectra.apply_derivative_preset"
    bl_label = "Build Derivative Template"
    bl_description = "Build a complete derivative teaching scene with graph, helpers, labels, HUD and timeline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            obj = _apply_template_and_build(context, "DERIVATIVE")
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Derivative template build failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built derivative template on {obj.name}")
        return {"FINISHED"}


class SPECTRA_OT_apply_integral_template(bpy.types.Operator):
    bl_idname = "spectra.apply_integral_template"
    bl_label = "Build Integral Template"
    bl_description = "Build a complete integral teaching scene with graph, area, labels, HUD and timeline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            obj = _apply_template_and_build(context, "INTEGRAL")
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Integral template build failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built integral template on {obj.name}")
        return {"FINISHED"}


class SPECTRA_OT_create_integral_visuals(bpy.types.Operator):
    bl_idname = "spectra.create_integral_visuals"
    bl_label = "Create Integral Visuals"
    bl_description = "Build integral area, bounds, HUD and accumulation graph for the selected curve"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_spectra_curve_object(context.active_object)

    def execute(self, context):
        settings = context.scene.spectra_settings
        obj = context.active_object
        try:
            create_or_update_integral_visuals(context, obj, settings)
        except FormulaValidationError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Integral build failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, "Integral visuals created")
        return {"FINISHED"}


CLASSES = (
    SPECTRA_OT_setup_scene,
    SPECTRA_OT_generate_graph,
    SPECTRA_OT_update_graph,
    SPECTRA_OT_clear_graphs,
    SPECTRA_OT_create_labels,
    SPECTRA_OT_sync_selected_to_panel,
    SPECTRA_OT_create_limit_visuals,
    SPECTRA_OT_create_calculus_visuals,
    SPECTRA_OT_apply_limit_template,
    SPECTRA_OT_apply_derivative_preset,
    SPECTRA_OT_apply_integral_template,
    SPECTRA_OT_create_integral_visuals,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
