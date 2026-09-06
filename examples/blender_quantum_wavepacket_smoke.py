"""Targeted Blender 5.2 smoke for the quantum probability + phase flagship.

Run from the repository root:

    blender --background --python examples/blender_quantum_wavepacket_smoke.py
"""

from __future__ import annotations

import bpy

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.showcases import QuantumWavepacketShowcaseConfig, build_quantum_wavepacket_scene


config = QuantumWavepacketShowcaseConfig(
    x_extent_m=4.0e-9,
    y_extent_m=3.0e-9,
    x_count=17,
    y_count=13,
    packet_center_x_m=-1.2e-9,
    packet_sigma_m=0.7e-9,
    wave_number_per_m=2.0e9,
    end_time_s=1.5e-15,
    steps=40,
    display_meters_per_unit=1.0e-9,
    probability_height_units=2.0,
    panel_gap_units=2.0,
)
scene = build_quantum_wavepacket_scene(config)
backend = QuantitativeBlenderBackend()
handle = backend.create(scene)

probability_id = "showcase.quantum.probability.surface"
phase_id = "showcase.quantum.phase.surface"
probability = bpy.data.objects[handle.object_names[probability_id]]
phase = bpy.data.objects[handle.object_names[phase_id]]

probability_object_pointer = probability.as_pointer()
probability_data_pointer = probability.data.as_pointer()
phase_object_pointer = phase.as_pointer()
phase_data_pointer = phase.data.as_pointer()

probability_color = probability.data.color_attributes.get("spectra_display_color")
phase_color = phase.data.color_attributes.get("spectra_display_color")
assert probability_color is not None
assert phase_color is not None
assert probability_color.domain == "POINT"
assert phase_color.domain == "POINT"
assert len(probability_color.data) == config.x_count * config.y_count
assert len(phase_color.data) == config.x_count * config.y_count
assert len(probability.data.materials) == 1
assert len(phase.data.materials) == 1

# Phase alpha intentionally fades low-probability regions.
phase_alpha = tuple(float(sample.color[3]) for sample in phase_color.data)
assert min(phase_alpha) < 0.2
assert max(phase_alpha) > 0.8

# A static no-op re-apply must preserve both quantitative mesh identities.
backend.apply(handle, scene)
updated_probability = bpy.data.objects[handle.object_names[probability_id]]
updated_phase = bpy.data.objects[handle.object_names[phase_id]]
assert updated_probability.as_pointer() == probability_object_pointer
assert updated_probability.data.as_pointer() == probability_data_pointer
assert updated_phase.as_pointer() == phase_object_pointer
assert updated_phase.data.as_pointer() == phase_data_pointer
assert updated_probability.data.color_attributes.get("spectra_display_color") is not None
assert updated_phase.data.color_attributes.get("spectra_display_color") is not None

collection_name = handle.collection_name
backend.destroy(handle)
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra quantum flagship Blender smoke PASS:",
    f"2 x {config.x_count * config.y_count} vertex-color samples,",
    "probability/phase mesh identity preserved, phase alpha mask preserved, cleanup PASS",
)
