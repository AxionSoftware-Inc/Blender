"""Targeted Blender 5.2 smoke for Spectra quantitative presentation.

Run from the repository root inside Blender, for example:

    blender --background --python examples/blender_quantitative_smoke.py

This validation intentionally imports ``bpy`` only to inspect the native
resources produced by the public Spectra backend. Scientific construction and
presentation remain renderer-independent.
"""

from __future__ import annotations

import bpy

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.primitives import PointCloud
from spectra.core.scene import Scene
from spectra.core.types import Vec3
from spectra.presentation import compose_presentation
from spectra.presentation_models import PresentationContext


def build_scene(values: tuple[float, ...]) -> Scene:
    positions = tuple(
        Vec3(float(index % 20) * 0.12, float(index // 20) * 0.12, 0.0)
        for index in range(len(values))
    )
    temperature = VisualAttribute(
        name="temperature",
        association="instance",
        kind="scalar",
        values=values,
        quantity_id="temperature",
    )
    cloud = PointCloud(
        id="quantitative.cloud",
        positions=positions,
        radius=0.035,
        attributes=VisualAttributeSet((temperature,)),
    )
    return compose_presentation(
        Scene(primitives=(cloud,)),
        "publication",
        context=PresentationContext(
            quantity_role="temperature",
            title="Quantitative PointCloud",
        ),
    )


values = tuple(float(index) for index in range(300))
scene = build_scene(values)
backend = QuantitativeBlenderBackend()
handle = backend.create(scene)

object_name = handle.object_names["quantitative.cloud"]
obj = bpy.data.objects[object_name]
mesh = obj.data
object_pointer = obj.as_pointer()
data_pointer = mesh.as_pointer()

attribute = mesh.color_attributes.get("spectra_display_color")
assert attribute is not None, "native mesh color attribute was not created"
assert attribute.domain == "POINT"
assert len(attribute.data) == 300 * 6
assert len(mesh.materials) == 1, "quantitative cloud should use one shader material"
assert len(handle.object_names) < 40, "quantitative presentation expanded into too many objects"

# Reverse only scalar values. Geometry/object/datablock identities must remain
# stable while the native color buffer is updated in place.
updated = build_scene(tuple(reversed(values)))
backend.apply(handle, updated)

updated_obj = bpy.data.objects[handle.object_names["quantitative.cloud"]]
assert updated_obj.as_pointer() == object_pointer
assert updated_obj.data.as_pointer() == data_pointer
updated_attribute = updated_obj.data.color_attributes.get("spectra_display_color")
assert updated_attribute is not None
assert len(updated_attribute.data) == 300 * 6
assert len(updated_obj.data.materials) == 1

collection_name = handle.collection_name
backend.destroy(handle)
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra quantitative Blender smoke PASS:",
    "300 values -> one PointCloud object, one material, native color attribute,",
    "color-only identity preserved, cleanup PASS",
)
