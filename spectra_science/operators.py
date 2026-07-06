import bpy

from .graph_builders import (
    build_curve_graph,
    is_spectra_object,
    build_surface_graph,
    update_graph_object,
)
from .math_parser import FormulaValidationError
from .scene_tools import animate_graph, create_labels, setup_scene


class SPECTRA_OT_setup_scene(bpy.types.Operator):
    bl_idname = "spectra.setup_scene"
    bl_label = "Setup Scientific Scene"
    bl_description = "Prepare a clean 2D or 3D scene for scientific work"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.spectra_settings
        setup_scene(context, settings.scene_mode)
        self.report({"INFO"}, f"Scene prepared in {settings.scene_mode[-2:]} mode")
        return {"FINISHED"}


class SPECTRA_OT_generate_graph(bpy.types.Operator):
    bl_idname = "spectra.generate_graph"
    bl_label = "Generate Graph"
    bl_description = "Create a graph object from the current formula"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.spectra_settings
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
        self.report({"INFO"}, f"Updated {obj.name}")
        return {"FINISHED"}


class SPECTRA_OT_clear_graphs(bpy.types.Operator):
    bl_idname = "spectra.clear_graphs"
    bl_label = "Clear Graphs"
    bl_description = "Remove generated Spectra graph objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        collection = bpy.data.collections.get(context.scene.spectra_settings.collection_name)
        if collection is None:
            self.report({"INFO"}, "No graph collection found")
            return {"CANCELLED"}

        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

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
        settings.graph_mode = obj.get("spectra_mode", settings.graph_mode)
        settings.scene_mode = obj.get("spectra_scene_mode", settings.scene_mode)
        settings.collection_name = obj.get("spectra_collection_name", settings.collection_name)
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
        self.report({"INFO"}, "Loaded selected Spectra settings into the panel")
        return {"FINISHED"}


CLASSES = (
    SPECTRA_OT_setup_scene,
    SPECTRA_OT_generate_graph,
    SPECTRA_OT_update_graph,
    SPECTRA_OT_clear_graphs,
    SPECTRA_OT_create_labels,
    SPECTRA_OT_sync_selected_to_panel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
