"""Animated Spectra wave -> Blender timeline smoke scene.

Run inside Blender later, for example:
    blender --python examples/blender_wave_animation.py

This file intentionally never imports bpy. Blender transport frames are bridged
through BlenderTimelineController while Spectra remains the owner of scientific
time and animation evaluation.
"""

import math

from spectra.backends import BlenderTimelineController
from spectra.core.framing import with_fitted_camera
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import Interval
from spectra.domains.physics import HarmonicWave1D, WaveAnimation1D


registry = DomainRegistry()
catalog = builtin_domain_catalog()
catalog.load(registry, ["physics.waves"])

wave = HarmonicWave1D(
    amplitude=1.0,
    wavelength=2.0 * math.pi,
    frequency=0.5,
    domain=Interval(-2.0 * math.pi, 2.0 * math.pi),
    name="traveling-wave",
)
animation = WaveAnimation1D(
    wave=wave,
    start_time=0.0,
    end_time=4.0,
    spatial_samples=256,
    temporal_samples=121,
    name="wave.curve",
)
scene = registry.compile_scene(animation)
scene = with_fitted_camera(
    scene,
    camera_id="camera.main",
    aspect_ratio=16.0 / 9.0,
    direction=Vec3(0.8, -1.0, 0.65),
    padding=1.25,
)

controller = BlenderTimelineController.bind(
    scene,
    fps=30.0,
    start_frame=1,
    set_blender_frame_range=True,
)

print(
    "Spectra animated wave bound to Blender frames",
    controller.start_frame,
    "through",
    controller.end_frame,
    "for",
    controller.duration,
    "seconds of engine time",
)
