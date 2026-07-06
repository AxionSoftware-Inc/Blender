bl_info = {
    "name": "Spectra Science",
    "author": "OpenAI Codex",
    "version": (0, 2, 1),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Spectra",
    "description": "Scientific graphing and animation foundation for Blender.",
    "category": "Object",
}

from . import operators, properties, runtime, ui


MODULES = (properties, operators, ui, runtime)


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
