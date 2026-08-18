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

    active_template: EnumProperty(
        name="Template",
        items=[
            ("LIMIT", "Limit", "Limit-focused teaching template"),
            ("DERIVATIVE", "Derivative", "Derivative-focused teaching template"),
            ("INTEGRAL", "Integral", "Integral-focused teaching template"),
            ("CUSTOM", "Custom", "Custom graph and scene settings"),
        ],
        default="DERIVATIVE",
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

    coordinate_extent: IntProperty(
        name="Axis Extent",
        default=10,
        min=2,
        max=100,
    )

    coordinate_step: FloatProperty(
        name="Tick Step",
        default=1.0,
        min=0.1,
        max=100.0,
    )

    coordinate_unit_scale: FloatProperty(
        name="Unit Scale",
        default=1.0,
        min=0.05,
        max=50.0,
    )

    coordinate_show_grid: BoolProperty(
        name="Show Grid",
        default=True,
    )

    coordinate_show_tick_labels: BoolProperty(
        name="Show Tick Labels",
        default=True,
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

    calculus_x: FloatProperty(
        name="x0",
        default=0.0,
    )

    calculus_h: FloatProperty(
        name="h",
        default=1.0,
        min=0.0001,
    )

    calculus_line_span: FloatProperty(
        name="Line Span",
        default=1.75,
        min=0.05,
    )

    show_moving_point: BoolProperty(
        name="Moving Point",
        default=True,
    )

    show_secant: BoolProperty(
        name="Secant",
        default=True,
    )

    show_tangent: BoolProperty(
        name="Tangent",
        default=True,
    )

    show_area: BoolProperty(
        name="Area Under Curve",
        default=False,
    )

    area_x_min: FloatProperty(
        name="Area Start",
        default=-2.0,
    )

    area_x_max: FloatProperty(
        name="Area End",
        default=2.0,
    )

    area_samples: IntProperty(
        name="Area Samples",
        default=64,
        min=8,
        max=512,
    )

    animate_calculus_x: BoolProperty(
        name="Animate x0",
        default=False,
    )

    calculus_x_start: FloatProperty(
        name="x0 Start",
        default=-3.0,
    )

    calculus_x_end: FloatProperty(
        name="x0 End",
        default=3.0,
    )

    calculus_frame_start: IntProperty(
        name="Calc Start",
        default=1,
        min=1,
        max=100000,
    )

    calculus_frame_end: IntProperty(
        name="Calc End",
        default=96,
        min=1,
        max=100000,
    )

    calculus_point_size: FloatProperty(
        name="Point Size",
        default=0.18,
        min=0.01,
        max=2.0,
    )

    derivative_show_hud: BoolProperty(
        name="Derivative HUD",
        default=True,
    )

    derivative_show_tangent_formula: BoolProperty(
        name="Tangent Formula",
        default=True,
    )

    derivative_show_point_label: BoolProperty(
        name="Point Label",
        default=True,
    )

    derivative_show_angle_guide: BoolProperty(
        name="Angle Guide",
        default=True,
    )

    derivative_hud_scale: FloatProperty(
        name="HUD Scale",
        default=0.58,
        min=0.05,
        max=4.0,
    )

    limit_target_x: FloatProperty(
        name="Limit x0",
        default=1.0,
    )

    limit_mode: EnumProperty(
        name="Limit Mode",
        items=[
            ("TWO_SIDED", "Two-Sided", "Approach the target from both left and right"),
            ("LEFT_ONLY", "Left Only", "Approach only from the left"),
            ("RIGHT_ONLY", "Right Only", "Approach only from the right"),
        ],
        default="TWO_SIDED",
    )

    animate_limit: BoolProperty(
        name="Animate Limit",
        default=False,
    )

    limit_distance_start: FloatProperty(
        name="Start Distance",
        default=2.0,
        min=0.0001,
    )

    limit_distance_end: FloatProperty(
        name="End Distance",
        default=0.05,
        min=0.00001,
    )

    limit_frame_start: IntProperty(
        name="Limit Start",
        default=1,
        min=1,
        max=100000,
    )

    limit_frame_end: IntProperty(
        name="Limit End",
        default=96,
        min=1,
        max=100000,
    )

    limit_estimate_tolerance: FloatProperty(
        name="Limit Tolerance",
        default=0.12,
        min=0.00001,
        max=1000.0,
    )

    show_limit_guides: BoolProperty(
        name="Limit Guides",
        default=True,
    )

    show_limit_hud: BoolProperty(
        name="Limit HUD",
        default=True,
    )

    limit_hud_scale: FloatProperty(
        name="Limit HUD Scale",
        default=0.58,
        min=0.05,
        max=4.0,
    )

    limit_show_hole: BoolProperty(
        name="Hole Marker",
        default=False,
    )

    limit_hole_y: FloatProperty(
        name="Hole Y",
        default=0.0,
    )

    limit_show_target_point: BoolProperty(
        name="Target Point",
        default=False,
    )

    limit_target_point_y: FloatProperty(
        name="Target Point Y",
        default=0.0,
    )

    show_derivative_graph: BoolProperty(
        name="Derivative Graph",
        default=False,
    )

    derivative_graph_offset_y: FloatProperty(
        name="Graph Offset Y",
        default=-5.0,
    )

    derivative_graph_scale_y: FloatProperty(
        name="Graph Scale Y",
        default=1.0,
        min=0.01,
    )

    animate_secant_h: BoolProperty(
        name="Animate h -> 0",
        default=False,
    )

    secant_h_start: FloatProperty(
        name="h Start",
        default=1.5,
        min=0.0001,
    )

    secant_h_end: FloatProperty(
        name="h End",
        default=0.05,
        min=0.00001,
    )

    secant_frame_start: IntProperty(
        name="h Start Frame",
        default=1,
        min=1,
        max=100000,
    )

    secant_frame_end: IntProperty(
        name="h End Frame",
        default=72,
        min=1,
        max=100000,
    )

    integral_a: FloatProperty(
        name="a",
        default=-2.0,
    )

    integral_b: FloatProperty(
        name="b",
        default=2.0,
    )

    integral_samples: IntProperty(
        name="Integral Samples",
        default=128,
        min=8,
        max=2048,
    )

    show_integral_area: BoolProperty(
        name="Show Area",
        default=True,
    )

    show_integral_bound_lines: BoolProperty(
        name="Bound Lines",
        default=True,
    )

    show_integral_bound_points: BoolProperty(
        name="Bound Points",
        default=True,
    )

    show_integral_hud: BoolProperty(
        name="Integral HUD",
        default=True,
    )

    integral_hud_scale: FloatProperty(
        name="Integral HUD Scale",
        default=0.58,
        min=0.05,
        max=4.0,
    )

    integral_scene_mode: EnumProperty(
        name="Integral Mode",
        items=[
            ("SIGNED_AREA", "Signed Area", "Focus on signed area under the curve"),
            ("ACCUMULATION", "Accumulation", "Focus on the accumulation function graph"),
            ("FTC", "FTC Bridge", "Show the Fundamental Theorem bridge visually"),
        ],
        default="SIGNED_AREA",
    )

    integral_value_mode: EnumProperty(
        name="Value Display",
        items=[
            ("SIGNED", "Signed", "Display signed area only"),
            ("ABSOLUTE", "Absolute", "Display absolute area only"),
            ("BOTH", "Both", "Display both signed and absolute area"),
        ],
        default="BOTH",
    )

    integral_animation_mode: EnumProperty(
        name="Bound Animation",
        items=[
            ("NONE", "None", "Keep both bounds fixed"),
            ("UPPER", "Upper Only", "Animate the upper bound while the lower bound stays fixed"),
            ("BOTH", "Both Bounds", "Animate both lower and upper bounds"),
        ],
        default="NONE",
    )

    integral_lower_start: FloatProperty(
        name="a Start",
        default=-2.0,
    )

    integral_lower_end: FloatProperty(
        name="a End",
        default=-1.0,
    )

    integral_upper_start: FloatProperty(
        name="b Start",
        default=-2.0,
    )

    integral_upper_end: FloatProperty(
        name="b End",
        default=2.0,
    )

    integral_frame_start: IntProperty(
        name="Integral Start",
        default=1,
        min=1,
        max=100000,
    )

    integral_frame_end: IntProperty(
        name="Integral End",
        default=96,
        min=1,
        max=100000,
    )

    integral_show_accumulation_graph: BoolProperty(
        name="Accumulation Graph",
        default=False,
    )

    integral_graph_offset_y: FloatProperty(
        name="Integral Graph Offset Y",
        default=-7.0,
    )

    integral_graph_scale_y: FloatProperty(
        name="Integral Graph Scale Y",
        default=1.0,
        min=0.01,
    )

    integral_show_strip_preview: BoolProperty(
        name="Strip Preview",
        default=False,
    )

    integral_strip_count: IntProperty(
        name="Strip Count",
        default=12,
        min=2,
        max=256,
    )

    ui_show_graph_advanced: BoolProperty(
        name="Graph Advanced",
        default=False,
    )

    ui_show_animation_advanced: BoolProperty(
        name="Animation Advanced",
        default=False,
    )

    ui_show_label_advanced: BoolProperty(
        name="Label Advanced",
        default=False,
    )

    ui_show_calculus_advanced: BoolProperty(
        name="Calculus Advanced",
        default=False,
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
