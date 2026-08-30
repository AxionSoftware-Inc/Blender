"""Composed electric + magnetic plane-wave animation for Blender.

Run inside Blender later:
    blender --python examples/blender_em_wave_animation.py

No bpy import is needed in this script. E and B are independent mathematical
vector-field animations, namespaced/composed into one Spectra Scene, then driven
by the incremental Blender timeline adapter.
"""

from spectra.backends import BlenderTimelineController
from spectra.core.composition import compose_namespaced_scenes
from spectra.core.framing import with_fitted_camera
from spectra.core.types import Color, Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import AxisSample, RegularGrid3D, TimeVectorFieldAnimation3D
from spectra.domains.mathematics.field_visualization import compile_time_vector_field_animation_scene
from spectra.domains.physics import PlaneElectromagneticWave


registry = DomainRegistry()
builtin_domain_catalog().load(registry, ["electromagnetism"])

# Use a normalized propagation speed for a visually readable demonstration.
# The semantic model also supports the SI vacuum default c = 299,792,458 m/s.
wave = PlaneElectromagneticWave(
    electric_amplitude=1.0,
    wavelength=4.0,
    propagation_direction=Vec3(0.0, 0.0, 1.0),
    polarization=Vec3(1.0, 0.0, 0.0),
    speed=2.0,
    name="plane-wave",
)
grid = RegularGrid3D(
    AxisSample(0.0, 0.0, 1),
    AxisSample(0.0, 0.0, 1),
    AxisSample(-6.0, 6.0, 25),
)

electric_view = TimeVectorFieldAnimation3D(
    field=wave.electric_field(),
    grid=grid,
    start_time=0.0,
    end_time=4.0,
    temporal_samples=121,
    vector_scale=1.0,
    name="field",
)
magnetic_view = TimeVectorFieldAnimation3D(
    field=wave.magnetic_field(),
    grid=grid,
    start_time=0.0,
    end_time=4.0,
    temporal_samples=121,
    # B0 = E0 / speed; this presentation scale makes E/B arrow lengths comparable.
    vector_scale=wave.speed,
    name="field",
)

electric_scene = compile_time_vector_field_animation_scene(
    electric_view,
    color=Color(0.25, 0.65, 1.0, 1.0),
)
magnetic_scene = compile_time_vector_field_animation_scene(
    magnetic_view,
    color=Color(1.0, 0.4, 0.25, 1.0),
)
scene = compose_namespaced_scenes(
    (
        ("electric", electric_scene),
        ("magnetic", magnetic_scene),
    )
)
scene = with_fitted_camera(
    scene,
    camera_id="camera.main",
    aspect_ratio=16.0 / 9.0,
    direction=Vec3(1.0, -1.2, 0.7),
    padding=1.35,
)

controller = BlenderTimelineController.bind(scene, fps=30.0, start_frame=1)
print(
    "Spectra EM wave scene bound to Blender:",
    len(scene.primitives),
    "primitives,",
    controller.duration,
    "seconds",
)
