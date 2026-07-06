import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty


class SpectraSettings(bpy.types.PropertyGroup):
    scene_mode: EnumProperty(
        name="Scene Mode",
        items=[
            ("MODE_2D", "2D", "Orthographic scientific scene"),
            ("MODE_3D", "3D", "Perspective scene for surfaces and 3D graphs"),
        ],
        default="MODE_2D",
    )

    graph_mode: EnumProperty(
        name="Graph Type",
        items=[
            ("CURVE_2D", "y = f(x)", "Sample a single-variable expression"),
            ("SURFACE_3D", "z = f(x, y)", "Sample a two-variable surface"),
        ],
        default="CURVE_2D",
    )

    expression: StringProperty(
        name="Formula",
        default="sin(x)",
        description="Use x, y and t variables with functions like sin, cos, exp, sqrt",
    )

    x_min: FloatProperty(name="X Min", default=-6.0)
    x_max: FloatProperty(name="X Max", default=6.0)
    y_min: FloatProperty(name="Y Min", default=-6.0)
    y_max: FloatProperty(name="Y Max", default=6.0)

    samples: IntProperty(name="Samples", default=128, min=16, max=4096)
    samples_x: IntProperty(name="X Samples", default=64, min=8, max=512)
    samples_y: IntProperty(name="Y Samples", default=64, min=8, max=512)

    curve_thickness: FloatProperty(
        name="Curve Thickness",
        default=0.02,
        min=0.0,
        max=1.0,
    )

    frame_rate_hint: FloatProperty(
        name="Time Scale",
        description="Scene frame divided by this value becomes t in formulas",
        default=24.0,
        min=1.0,
        max=240.0,
    )

    collection_name: StringProperty(
        name="Collection",
        default="Spectra Graphs",
    )

    animate_on_create: BoolProperty(
        name="Animate Graph",
        default=True,
        description="Animate the graph when it is created",
    )

    animation_style: EnumProperty(
        name="Animation Style",
        items=[
            ("DRAW", "Draw", "Reveal the graph progressively"),
            ("RISE", "Rise", "Lift the graph into place"),
        ],
        default="DRAW",
    )

    animation_start: IntProperty(
        name="Start Frame",
        default=1,
        min=1,
        max=100000,
    )

    animation_duration: IntProperty(
        name="Duration",
        default=48,
        min=1,
        max=100000,
    )

    show_labels: BoolProperty(
        name="Show Labels",
        default=True,
        description="Create title and formula labels in the scene",
    )

    title_text: StringProperty(
        name="Title",
        default="Scientific Graph",
    )

    formula_label: StringProperty(
        name="Formula Label",
        default="",
        description="If empty, the main formula is reused",
    )

    label_size: FloatProperty(
        name="Label Size",
        default=0.65,
        min=0.05,
        max=10.0,
    )

    parameter_values: StringProperty(
        name="Parameters",
        default="",
        description="Comma-separated values like a=1, b=2.5",
    )

    live_formula_animation: BoolProperty(
        name="Live Formula Animation",
        default=False,
        description="Recalculate selected Spectra objects when the frame changes",
    )

    parameter_animation_enabled: BoolProperty(
        name="Animate Parameter",
        default=False,
        description="Sweep one parameter across a frame range",
    )

    animated_parameter: StringProperty(
        name="Parameter Name",
        default="a",
    )

    animated_parameter_start: FloatProperty(
        name="Start Value",
        default=0.0,
    )

    animated_parameter_end: FloatProperty(
        name="End Value",
        default=1.0,
    )

    parameter_frame_start: IntProperty(
        name="Param Start",
        default=1,
        min=1,
        max=100000,
    )

    parameter_frame_end: IntProperty(
        name="Param End",
        default=96,
        min=1,
        max=100000,
    )


CLASSES = (SpectraSettings,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.spectra_settings = PointerProperty(type=SpectraSettings)


def unregister():
    del bpy.types.Scene.spectra_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
