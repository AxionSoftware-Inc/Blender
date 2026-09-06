"""Targeted Blender 5.2 smoke for the thermoelastic heated-bar flagship.

Run from the repository root:

    blender --background --python examples/blender_thermoelastic_bar_smoke.py
"""

from __future__ import annotations

import bpy

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.core.primitives import Surface
from spectra.showcases import ThermoelasticBarShowcaseConfig, build_thermoelastic_bar_scene


config = ThermoelasticBarShowcaseConfig(
    x_count=7,
    y_count=3,
    z_count=3,
    steps=12,
    end_time_s=8.0,
    deformation_exaggeration=40.0,
)
scene = build_thermoelastic_bar_scene(config)
surface_id = "showcase.thermoelastic.bar.surface"
surface = scene.get(surface_id)
assert isinstance(surface, Surface)
assert surface.attributes.get("temperature").quantity_id == "temperature"
assert surface.attributes.get("thermal_strain").quantity_id == "thermal_strain"
assert surface.attributes.get("display_color").quantity_id == "temperature"

backend = QuantitativeBlenderBackend()
handle = backend.create(scene)
bar = bpy.data.objects[handle.object_names[surface_id]]

object_pointer = bar.as_pointer()
data_pointer = bar.data.as_pointer()
color_attribute = bar.data.color_attributes.get("spectra_display_color")
assert color_attribute is not None
assert color_attribute.domain == "POINT"
assert len(color_attribute.data) == len(surface.vertices)
assert len(bar.data.materials) == 1

scene_max_x = max(vertex.x for vertex in surface.vertices)
native_max_x = max(float(vertex.co.x) for vertex in bar.data.vertices)
assert native_max_x > 0.5 * config.length_m
assert abs(native_max_x - scene_max_x) < 1e-6

# A static no-op re-apply must preserve the quantitative mesh identity and data.
backend.apply(handle, scene)
updated_bar = bpy.data.objects[handle.object_names[surface_id]]
assert updated_bar.as_pointer() == object_pointer
assert updated_bar.data.as_pointer() == data_pointer
updated_color = updated_bar.data.color_attributes.get("spectra_display_color")
assert updated_color is not None
assert len(updated_color.data) == len(surface.vertices)

collection_name = handle.collection_name
backend.destroy(handle)
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra thermoelastic flagship Blender smoke PASS:",
    f"{len(surface.vertices)} quantitative surface vertices,",
    "deformed geometry preserved, mesh identity preserved, cleanup PASS",
)
