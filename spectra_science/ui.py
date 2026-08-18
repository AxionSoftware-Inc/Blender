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

        row = layout.row(align=True)
        row.operator("spectra.apply_limit_template", text="Limit Scene", icon="PRESET")
        row.operator("spectra.apply_derivative_preset", text="Derivative Scene", icon="PRESET")
        row.operator("spectra.apply_integral_template", text="Integral Scene", icon="PRESET")
        layout.prop(settings, "active_template")
        layout.prop(settings, "scene_mode")
        row = layout.row(align=True)
        row.operator("spectra.setup_scene", icon="SCENE_DATA")
        row.operator("spectra.generate_graph", icon="CURVE_DATA")

        layout.separator()
        layout.prop(settings, "graph_mode")
        layout.prop(settings, "expression")

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

        if settings.active_template == "LIMIT":
            calc_box = layout.box()
            calc_box.label(text="Limit")
            calc_box.prop(settings, "limit_target_x")
            calc_box.prop(settings, "limit_mode")
            calc_box.prop(settings, "animate_limit")
            calc_box.prop(settings, "show_limit_hud")
        elif settings.active_template == "INTEGRAL":
            calc_box = layout.box()
            calc_box.label(text="Integral")
            calc_box.prop(settings, "integral_a")
            calc_box.prop(settings, "integral_b")
            calc_box.prop(settings, "show_integral_area")
            calc_box.prop(settings, "integral_animation_mode")
            calc_box.prop(settings, "show_integral_hud")
        else:
            calc_box = layout.box()
            calc_box.label(text="Derivative")
            calc_box.prop(settings, "calculus_x")
            calc_box.prop(settings, "calculus_h")
            calc_box.prop(settings, "show_moving_point")
            calc_box.prop(settings, "show_secant")
            calc_box.prop(settings, "show_tangent")
            calc_box.prop(settings, "show_derivative_graph")
            calc_box.prop(settings, "derivative_show_hud")
            calc_box.prop(settings, "animate_calculus_x")
            if settings.animate_calculus_x:
                calc_box.prop(settings, "calculus_x_start")
                calc_box.prop(settings, "calculus_x_end")
            calc_box.prop(settings, "animate_secant_h")

        layout.separator()
        row = layout.row(align=True)
        row.operator("spectra.update_graph", icon="FILE_REFRESH")
        row.operator("spectra.sync_selected_to_panel", icon="IMPORT")
        if settings.active_template == "LIMIT":
            layout.operator("spectra.create_limit_visuals", icon="DRIVER_DISTANCE")
        elif settings.active_template == "INTEGRAL":
            layout.operator("spectra.create_integral_visuals", icon="MESH_GRID")
        else:
            layout.operator("spectra.create_calculus_visuals", icon="GP_SELECT_POINTS")
        layout.operator("spectra.clear_graphs", icon="TRASH")

        graph_adv = layout.box()
        graph_adv.prop(settings, "ui_show_graph_advanced", icon="DISCLOSURE_TRI_RIGHT" if not settings.ui_show_graph_advanced else "DISCLOSURE_TRI_DOWN")
        if settings.ui_show_graph_advanced:
            graph_adv.prop(settings, "frame_rate_hint")
            graph_adv.prop(settings, "coordinate_extent")
            graph_adv.prop(settings, "coordinate_step")
            graph_adv.prop(settings, "coordinate_unit_scale")
            graph_adv.prop(settings, "coordinate_show_grid")
            graph_adv.prop(settings, "coordinate_show_tick_labels")
            graph_adv.prop(settings, "x_min")
            graph_adv.prop(settings, "x_max")
            if settings.graph_mode == "CURVE_2D":
                graph_adv.prop(settings, "samples")
                graph_adv.prop(settings, "curve_thickness")
            else:
                graph_adv.prop(settings, "y_min")
                graph_adv.prop(settings, "y_max")
                graph_adv.prop(settings, "samples_x")
                graph_adv.prop(settings, "samples_y")

        anim_adv = layout.box()
        anim_adv.prop(settings, "ui_show_animation_advanced", icon="DISCLOSURE_TRI_RIGHT" if not settings.ui_show_animation_advanced else "DISCLOSURE_TRI_DOWN")
        if settings.ui_show_animation_advanced:
            anim_adv.prop(settings, "animate_on_create")
            if settings.animate_on_create:
                anim_adv.prop(settings, "animation_style")
                anim_adv.prop(settings, "animation_start")
                anim_adv.prop(settings, "animation_duration")
            anim_adv.prop(settings, "live_formula_animation")
            anim_adv.prop(settings, "parameter_animation_enabled")
            if settings.parameter_animation_enabled:
                anim_adv.prop(settings, "animated_parameter")
                anim_adv.prop(settings, "animated_parameter_start")
                anim_adv.prop(settings, "animated_parameter_end")
                anim_adv.prop(settings, "parameter_frame_start")
                anim_adv.prop(settings, "parameter_frame_end")
            if settings.animate_limit:
                anim_adv.prop(settings, "limit_distance_start")
                anim_adv.prop(settings, "limit_distance_end")
                anim_adv.prop(settings, "limit_frame_start")
                anim_adv.prop(settings, "limit_frame_end")
            if settings.animate_calculus_x:
                anim_adv.prop(settings, "calculus_frame_start")
                anim_adv.prop(settings, "calculus_frame_end")
            if settings.animate_secant_h:
                anim_adv.prop(settings, "secant_h_start")
                anim_adv.prop(settings, "secant_h_end")
                anim_adv.prop(settings, "secant_frame_start")
                anim_adv.prop(settings, "secant_frame_end")

        label_adv = layout.box()
        label_adv.prop(settings, "ui_show_label_advanced", icon="DISCLOSURE_TRI_RIGHT" if not settings.ui_show_label_advanced else "DISCLOSURE_TRI_DOWN")
        if settings.ui_show_label_advanced:
            label_adv.prop(settings, "show_labels")
            label_adv.prop(settings, "title_text")
            label_adv.prop(settings, "formula_label")
            label_adv.prop(settings, "label_size")
            label_adv.prop(settings, "derivative_show_tangent_formula")
            label_adv.prop(settings, "derivative_show_point_label")
            label_adv.prop(settings, "derivative_show_angle_guide")
            label_adv.prop(settings, "derivative_hud_scale")

        calc_adv = layout.box()
        calc_adv.prop(settings, "ui_show_calculus_advanced", icon="DISCLOSURE_TRI_RIGHT" if not settings.ui_show_calculus_advanced else "DISCLOSURE_TRI_DOWN")
        if settings.ui_show_calculus_advanced:
            calc_adv.prop(settings, "parameter_values")
            if settings.active_template == "LIMIT":
                calc_adv.prop(settings, "show_limit_guides")
                calc_adv.prop(settings, "limit_hud_scale")
                calc_adv.prop(settings, "limit_estimate_tolerance")
                calc_adv.prop(settings, "limit_show_hole")
                if settings.limit_show_hole:
                    calc_adv.prop(settings, "limit_hole_y")
                calc_adv.prop(settings, "limit_show_target_point")
                if settings.limit_show_target_point:
                    calc_adv.prop(settings, "limit_target_point_y")
            elif settings.active_template == "INTEGRAL":
                calc_adv.prop(settings, "integral_samples")
                calc_adv.prop(settings, "integral_scene_mode")
                calc_adv.prop(settings, "integral_value_mode")
                calc_adv.prop(settings, "show_integral_bound_lines")
                calc_adv.prop(settings, "show_integral_bound_points")
                calc_adv.prop(settings, "integral_hud_scale")
                calc_adv.prop(settings, "integral_show_accumulation_graph")
                if settings.integral_show_accumulation_graph:
                    calc_adv.prop(settings, "integral_graph_offset_y")
                    calc_adv.prop(settings, "integral_graph_scale_y")
                calc_adv.prop(settings, "integral_show_strip_preview")
                if settings.integral_show_strip_preview:
                    calc_adv.prop(settings, "integral_strip_count")
                if settings.integral_animation_mode != "NONE":
                    calc_adv.prop(settings, "integral_frame_start")
                    calc_adv.prop(settings, "integral_frame_end")
                    calc_adv.prop(settings, "integral_upper_start")
                    calc_adv.prop(settings, "integral_upper_end")
                    if settings.integral_animation_mode == "BOTH":
                        calc_adv.prop(settings, "integral_lower_start")
                        calc_adv.prop(settings, "integral_lower_end")
            else:
                calc_adv.prop(settings, "calculus_line_span")
                calc_adv.prop(settings, "calculus_point_size")
                calc_adv.prop(settings, "show_area")
                if settings.show_area:
                    calc_adv.prop(settings, "area_x_min")
                    calc_adv.prop(settings, "area_x_max")
                    calc_adv.prop(settings, "area_samples")
                if settings.show_derivative_graph:
                    calc_adv.prop(settings, "derivative_graph_offset_y")
                    calc_adv.prop(settings, "derivative_graph_scale_y")

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
