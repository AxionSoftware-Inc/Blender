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
from spectra.core.types import Color, Vec3
from spectra.presentation import compose_presentation
from spectra.presentation_models import PresentationContext


def build_scene(
    values: tuple[float, ...],
    *,
    alpha_opacity: float = 1.0,
) -> Scene:
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

    # Direct display colors exercise the generic Scene-v5 color path, including
    # per-value alpha. This cloud intentionally has no temperature scalar so the
    # publication color-scale pass leaves its explicit display colors unchanged.
    alpha_values = (0.0, 0.25, 0.75, 1.0)
    alpha_colors = tuple(
        Color(1.0, 0.35, 0.1, alpha)
        for alpha in alpha_values
    )
    alpha_cloud = PointCloud(
        id="alpha.cloud",
        positions=tuple(
            Vec3(2.8 + index * 0.15, 0.0, 0.0)
            for index in range(len(alpha_colors))
        ),
        radius=0.055,
        opacity=alpha_opacity,
        attributes=VisualAttributeSet(
            (
                VisualAttribute(
                    name="display_color",
                    association="instance",
                    kind="color",
                    values=alpha_colors,
                    quantity_id="display_alpha",
                ),
            )
        ),
    )

    return compose_presentation(
        Scene(primitives=(cloud, alpha_cloud)),
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

# Per-value alpha must survive into Blender's native color buffer, and the
# quantitative material must contain a dynamic alpha multiply + transparent mix.
alpha_obj = bpy.data.objects[handle.object_names["alpha.cloud"]]
alpha_mesh = alpha_obj.data
alpha_object_pointer = alpha_obj.as_pointer()
alpha_data_pointer = alpha_mesh.as_pointer()
alpha_attribute = alpha_mesh.color_attributes.get("spectra_display_color")
assert alpha_attribute is not None
assert len(alpha_attribute.data) == 4 * 6
observed_alphas = tuple(float(alpha_attribute.data[index * 6].color[3]) for index in range(4))
expected_alphas = (0.0, 0.25, 0.75, 1.0)
for observed, expected in zip(observed_alphas, expected_alphas, strict=True):
    assert abs(observed - expected) < 1e-5, (observed, expected)
assert len(alpha_mesh.materials) == 1
alpha_material = alpha_mesh.materials[0]
node_types = {node.type for node in alpha_material.node_tree.nodes}
assert "MATH" in node_types, "quantitative material must multiply attribute alpha"
assert "MIX_SHADER" in node_types, "quantitative material must mix transparency"
assert "BSDF_TRANSPARENT" in node_types, "quantitative material must support alpha transparency"
assert abs(float(alpha_material["spectra_opacity"]) - 1.0) < 1e-9

# Reverse scalar values and change only alpha-cloud primitive opacity. Geometry,
# object and datablock identities must remain stable while color/material state
# is updated through the quantitative adapter.
updated = build_scene(tuple(reversed(values)), alpha_opacity=0.5)
backend.apply(handle, updated)

updated_obj = bpy.data.objects[handle.object_names["quantitative.cloud"]]
assert updated_obj.as_pointer() == object_pointer
assert updated_obj.data.as_pointer() == data_pointer
updated_attribute = updated_obj.data.color_attributes.get("spectra_display_color")
assert updated_attribute is not None
assert len(updated_attribute.data) == 300 * 6
assert len(updated_obj.data.materials) == 1

updated_alpha_obj = bpy.data.objects[handle.object_names["alpha.cloud"]]
assert updated_alpha_obj.as_pointer() == alpha_object_pointer
assert updated_alpha_obj.data.as_pointer() == alpha_data_pointer
updated_alpha_attribute = updated_alpha_obj.data.color_attributes.get("spectra_display_color")
assert updated_alpha_attribute is not None
updated_alphas = tuple(float(updated_alpha_attribute.data[index * 6].color[3]) for index in range(4))
for observed, expected in zip(updated_alphas, expected_alphas, strict=True):
    assert abs(observed - expected) < 1e-5, (observed, expected)
updated_alpha_material = updated_alpha_obj.data.materials[0]
assert updated_alpha_material.as_pointer() == alpha_material.as_pointer()
assert abs(float(updated_alpha_material["spectra_opacity"]) - 0.5) < 1e-9

collection_name = handle.collection_name
backend.destroy(handle)
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra quantitative Blender smoke PASS:",
    "300 values -> one PointCloud object, one material, native color attribute,",
    "per-value alpha + opacity preserved, color-only/opacity-only identity preserved, cleanup PASS",
)
