import bpy

from .math_parser import FormulaValidationError, detect_parameters, resolve_parameter_scope


class SPECTRA_PT_main_panel(bpy.types.Panel):
    bl_label = "Spectra Science"
    bl_idname = "SPECTRA_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Spectra"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.spectra_settings

        layout.prop(settings, "scene_mode")
        layout.operator("spectra.setup_scene", icon="SCENE_DATA")

        layout.separator()
        layout.prop(settings, "graph_mode")
        layout.prop(settings, "expression")
        layout.prop(settings, "frame_rate_hint")

        try:
            detected = detect_parameters(settings.expression)
            detected_text = ", ".join(detected) if detected else "none"
            active_params = resolve_parameter_scope(context.scene.frame_current, settings)
            active_text = ", ".join(
                f"{name}={value:.3f}" for name, value in sorted(active_params.items())
            ) if active_params else "none"
            info = layout.box()
            info.label(text=f"Detected parameters: {detected_text}")
            info.label(text=f"Active values: {active_text}")
        except FormulaValidationError as exc:
            error_box = layout.box()
            error_box.label(text=f"Formula parse error: {exc}")

        box = layout.box()
        box.label(text="Domain")
        box.prop(settings, "x_min")
        box.prop(settings, "x_max")

        if settings.graph_mode == "CURVE_2D":
            box.prop(settings, "samples")
            box.prop(settings, "curve_thickness")
        else:
            box.prop(settings, "y_min")
            box.prop(settings, "y_max")
            box.prop(settings, "samples_x")
            box.prop(settings, "samples_y")

        anim_box = layout.box()
        anim_box.label(text="Animation")
        anim_box.prop(settings, "animate_on_create")
        if settings.animate_on_create:
            anim_box.prop(settings, "animation_style")
            anim_box.prop(settings, "animation_start")
            anim_box.prop(settings, "animation_duration")
        anim_box.prop(settings, "live_formula_animation")
        anim_box.prop(settings, "parameter_animation_enabled")
        if settings.parameter_animation_enabled:
            anim_box.prop(settings, "animated_parameter")
            anim_box.prop(settings, "animated_parameter_start")
            anim_box.prop(settings, "animated_parameter_end")
            anim_box.prop(settings, "parameter_frame_start")
            anim_box.prop(settings, "parameter_frame_end")

        param_box = layout.box()
        param_box.label(text="Parameters")
        param_box.prop(settings, "parameter_values")

        label_box = layout.box()
        label_box.label(text="Labels")
        label_box.prop(settings, "show_labels")
        label_box.prop(settings, "title_text")
        label_box.prop(settings, "formula_label")
        label_box.prop(settings, "label_size")

        layout.separator()
        layout.operator("spectra.generate_graph", icon="CURVE_DATA")
        layout.operator("spectra.update_graph", icon="FILE_REFRESH")
        layout.operator("spectra.sync_selected_to_panel", icon="IMPORT")
        layout.operator("spectra.create_labels", icon="FONT_DATA")
        layout.operator("spectra.clear_graphs", icon="TRASH")

        active = context.active_object
        if active and active.get("spectra_object"):
            info_box = layout.box()
            info_box.label(text=f"Selected: {active.name}")
            info_box.label(text=f"Mode: {active.get('spectra_mode', '-')}")
            info_box.label(text=f"Formula: {active.get('spectra_formula', '-')}")

        help_box = layout.box()
        help_box.label(text="Formula Tips")
        help_box.label(text="Variables: x, y, t")
        help_box.label(text="Functions: sin, cos, exp, sqrt")


CLASSES = (SPECTRA_PT_main_panel,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
