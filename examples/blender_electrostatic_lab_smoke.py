"""Targeted Blender 5.2 smoke for the electrostatic flagship scene.

Run from the repository root:

    blender --background --python examples/blender_electrostatic_lab_smoke.py

This script imports bpy only to inspect native resources. Scientific potential,
field construction, quantitative color mapping, and presentation are upstream.
"""

from __future__ import annotations

import bpy

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.showcases import (
    ElectrostaticLabShowcaseConfig,
    build_electrostatic_lab_scene,
)


config = ElectrostaticLabShowcaseConfig(
    extent_m=3.0,
    z_extent_m=1.0,
    source_offset_m=1.5,
    solver_grid_xy_count=11,
    solver_grid_z_count=5,
    slice_samples=25,
    vector_samples=7,
    field_line_seed_count=8,
    field_line_seed_radius_m=0.35,
    field_line_parameter_length=4.5,
    field_line_steps=40,
    max_iterations=3000,
    tolerance=1.0e-4,
)
scene = build_electrostatic_lab_scene(config)
backend = QuantitativeBlenderBackend()
handle = backend.create(scene)

surface_id = "showcase.electrostatic.potential.slice"
vector_id = "showcase.electrostatic.field.vectors"
surface = bpy.data.objects[handle.object_names[surface_id]]
vectors = bpy.data.objects[handle.object_names[vector_id]]

surface_object_pointer = surface.as_pointer()
surface_data_pointer = surface.data.as_pointer()
vector_object_pointer = vectors.as_pointer()
vector_data_pointer = vectors.data.as_pointer()

attribute = surface.data.color_attributes.get("spectra_display_color")
assert attribute is not None, "electrostatic potential Surface has no native quantitative color"
assert attribute.domain == "POINT"
assert len(attribute.data) == config.slice_samples ** 2
assert len(surface.data.materials) == 1, "potential Surface should use one quantitative material"

# Electric vectors remain one batched Curve representation in the current backend.
assert len(vectors.data.splines) == config.vector_samples ** 2

field_line_ids = tuple(
    primitive_id
    for primitive_id in handle.object_names
    if primitive_id.startswith("showcase.electrostatic.field_lines.curve_")
)
assert len(field_line_ids) == config.field_line_seed_count
assert "showcase.electrostatic.source.positive" in handle.object_names
assert "showcase.electrostatic.source.negative" in handle.object_names
assert len(handle.object_names) < 70, "electrostatic showcase expanded into too many Blender objects"

# A no-op static re-apply must preserve the key native identities.
backend.apply(handle, scene)
updated_surface = bpy.data.objects[handle.object_names[surface_id]]
updated_vectors = bpy.data.objects[handle.object_names[vector_id]]
assert updated_surface.as_pointer() == surface_object_pointer
assert updated_surface.data.as_pointer() == surface_data_pointer
assert updated_vectors.as_pointer() == vector_object_pointer
assert updated_vectors.data.as_pointer() == vector_data_pointer
assert updated_surface.data.color_attributes.get("spectra_display_color") is not None
assert len(updated_surface.data.materials) == 1

collection_name = handle.collection_name
backend.destroy(handle)
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra electrostatic flagship Blender smoke PASS:",
    f"{config.slice_samples ** 2} signed-potential colors -> one Surface/material,",
    f"{config.vector_samples ** 2} E vectors -> one batched Curve,",
    f"{config.field_line_seed_count} field lines, static identity preserved, cleanup PASS",
)
