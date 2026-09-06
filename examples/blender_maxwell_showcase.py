"""Canonical Spectra Maxwell flagship scene for Blender.

Run inside Blender from the repository root, for example:

    blender --python examples/blender_maxwell_showcase.py

The scientific Scene uses SI meters and seconds. The default two-period Maxwell
Timeline is only tens of nanoseconds long; Blender transport displays that exact
scientific interval over four presentation seconds without changing scientific
time.
"""

from spectra.backends import BlenderTimelineController
from spectra.showcases import MaxwellWaveShowcaseConfig, build_maxwell_wave_scene


config = MaxwellWaveShowcaseConfig()
scene = build_maxwell_wave_scene(config)
controller = BlenderTimelineController.bind(
    scene,
    fps=30.0,
    start_frame=1,
    playback_duration=config.playback_duration,
)

print(
    "Spectra Maxwell flagship bound to Blender:",
    f"scientific={config.scientific_duration * 1e9:.3f} ns,",
    f"playback={controller.playback_duration:.3f} s,",
    f"frames={controller.start_frame}..{controller.end_frame},",
    f"primitives={len(scene.primitives)}",
)
