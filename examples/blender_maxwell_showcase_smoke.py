"""Targeted Blender 5.2 smoke for the canonical Maxwell flagship scene.

Run from the repository root:

    blender --background --python examples/blender_maxwell_showcase_smoke.py

This script imports bpy only to inspect native resources. Scientific construction,
SI time, and presentation composition remain inside Spectra.
"""

from __future__ import annotations

import bpy

from spectra.backends import BlenderTimelineController
from spectra.showcases import MaxwellWaveShowcaseConfig, build_maxwell_wave_scene


config = MaxwellWaveShowcaseConfig(spatial_samples=49, temporal_samples=121)
scene = build_maxwell_wave_scene(config)
controller = BlenderTimelineController.bind(
    scene,
    fps=30.0,
    start_frame=1,
    playback_duration=config.playback_duration,
)
handle = controller.session.handle

assert abs(controller.duration - config.scientific_duration) < 1e-18
assert controller.playback_duration == config.playback_duration
assert controller.end_frame == 121
assert len(handle.object_names) < 40, "Maxwell showcase expanded into too many Blender objects"

ids = (
    "showcase.maxwell.electric.vectors",
    "showcase.maxwell.magnetic.vectors",
    "showcase.maxwell.electric.trace",
    "showcase.maxwell.magnetic.trace",
)
pointers: dict[str, tuple[int, int]] = {}
for primitive_id in ids:
    obj = bpy.data.objects[handle.object_names[primitive_id]]
    pointers[primitive_id] = (obj.as_pointer(), obj.data.as_pointer())

# E/B remain one batched Curve representation each in the current backend.
electric = bpy.data.objects[handle.object_names["showcase.maxwell.electric.vectors"]]
magnetic = bpy.data.objects[handle.object_names["showcase.maxwell.magnetic.vectors"]]
assert len(electric.data.splines) == config.spatial_samples
assert len(magnetic.data.splines) == config.spatial_samples

# Traverse a visible four-second Blender transport while Spectra samples only
# the exact nanosecond scientific interval.
for frame in (1, 31, 61, 91, 121):
    snapshot = controller.seek_frame(frame)
    assert snapshot.timeline.duration == 0.0
    for primitive_id in ids:
        obj = bpy.data.objects[handle.object_names[primitive_id]]
        object_pointer, data_pointer = pointers[primitive_id]
        assert obj.as_pointer() == object_pointer, (frame, primitive_id, "object identity")
        assert obj.data.as_pointer() == data_pointer, (frame, primitive_id, "datablock identity")

assert controller.session.time == config.scientific_duration
collection_name = handle.collection_name
controller.close()
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra Maxwell flagship Blender smoke PASS:",
    f"{config.spatial_samples} E + {config.spatial_samples} B glyphs remain batched,",
    f"{config.scientific_duration * 1e9:.3f} ns science -> {config.playback_duration:.1f} s playback,",
    "start/mid/end identity preserved, cleanup PASS",
)
