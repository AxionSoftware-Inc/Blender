import bpy
from bpy.app.handlers import persistent

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
            if not _should_refresh(obj):
                continue
            try:
                settings = settings_from_object(obj)
                update_graph_object(context, obj, settings)
            except FormulaValidationError:
                continue
            except Exception:
                continue
    finally:
        _is_refreshing = False


@persistent
def spectra_frame_change_handler(scene):
    refresh_animated_graphs(scene)


def register():
    handlers = bpy.app.handlers.frame_change_post
    if spectra_frame_change_handler not in handlers:
        handlers.append(spectra_frame_change_handler)


def unregister():
    handlers = bpy.app.handlers.frame_change_post
    if spectra_frame_change_handler in handlers:
        handlers.remove(spectra_frame_change_handler)
