import bpy
from bpy.app.handlers import persistent

from .calculus_tools import refresh_calculus_for_graph
from .graph_builders import is_spectra_object, settings_from_object, update_graph_object
from .math_parser import FormulaValidationError


_is_refreshing = False


def _should_refresh(obj):
    if not is_spectra_object(obj):
        return False
    settings = settings_from_object(obj)
    return bool(
        settings.live_formula_animation
        or settings.parameter_animation_enabled
        or "t" in settings.expression
    )


def refresh_animated_graphs(scene):
    global _is_refreshing
    if _is_refreshing:
        return

    _is_refreshing = True
    try:
        context = bpy.context
        for obj in bpy.data.objects:
            try:
                if _should_refresh(obj):
                    settings = settings_from_object(obj)
                    update_graph_object(context, obj, settings)
                if is_spectra_object(obj):
                    refresh_calculus_for_graph(context, obj)
            except FormulaValidationError:
                continue
            except Exception:
                continue
    finally:
        _is_refreshing = False


@persistent
def spectra_frame_change_handler(scene):
    refresh_animated_graphs(scene)


@persistent
def spectra_frame_change_pre_handler(scene, depsgraph=None):
    refresh_animated_graphs(scene)


def register():
    post_handlers = bpy.app.handlers.frame_change_post
    pre_handlers = bpy.app.handlers.frame_change_pre
    if spectra_frame_change_handler not in post_handlers:
        post_handlers.append(spectra_frame_change_handler)
    if spectra_frame_change_pre_handler not in pre_handlers:
        pre_handlers.append(spectra_frame_change_pre_handler)


def unregister():
    post_handlers = bpy.app.handlers.frame_change_post
    pre_handlers = bpy.app.handlers.frame_change_pre
    if spectra_frame_change_handler in post_handlers:
        post_handlers.remove(spectra_frame_change_handler)
    if spectra_frame_change_pre_handler in pre_handlers:
        pre_handlers.remove(spectra_frame_change_pre_handler)
