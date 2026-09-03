# Spectra Science — Blender Premium Source Audit

Status: **source audit of current runtime; no Blender/runtime code changed**.

This document records concrete facts from the current Blender backend implementation so future premium-presentation capability claims match actual code rather than design intent.

## Current backend contracts

Both:

```text
BlenderBackend
IncrementalBlenderBackend
```

currently advertise the existing generic `BackendCapabilities` contract with:

```text
all core primitive kinds
supports_group_hierarchy = true
supports_materials = true
```

Premium presentation should extend this one capability contract later rather than creating another renderer capability registry.

## Current primitive mappings

Source confirms:

```text
Point        -> mesh
a PointCloud -> one mesh object
Polyline     -> Curve
Surface      -> mesh
Region       -> mesh
VectorGlyph  -> Curve
VectorGlyphSet -> one Curve with many splines
TextLabel    -> FONT curve
Camera       -> Blender camera
Light        -> Blender light
Group        -> Empty organization node
```

Dense scientific values remain batched at object level.

## Camera mapping

Current generic Camera maps directly to:

```text
perspective -> PERSP + angle_y
orthographic -> ORTHO + ortho_scale
near/far clip
```

Therefore generic presentation camera fitting can be implemented without changing Blender backend camera semantics.

## Light mapping

Current generic lights map:

```text
ambient     -> AREA
directional -> SUN
point       -> POINT
spot        -> SPOT
```

Color, intensity, range, and spot angle are mapped with backend-specific scaling where needed.

This is sufficient for a first generic scientific-studio light rig.

## Material mapping

Current generic `Material` maps to Blender nodes:

```text
unlit -> Emission
lit   -> Principled BSDF
```

with support for:

```text
base color
metallic
roughness
emission
alpha/transparency
```

Therefore presentation materials can already express useful premium/basic styling.

## Current per-instance color path

`PointCloud.colors` and `VectorGlyphSet.colors` are supported in the reference Blender backend through material slots.

Important implementation guard:

```text
maximum unique colors per batched primitive: 256
```

If more than 256 unique colors are requested, the reference backend raises instead of creating thousands of materials.

### Consequence

Current support is suitable for:

- categorical coloring;
- bounded color classes;
- small discrete palettes.

It is **not** the final scalable path for:

- continuous temperature gradient with thousands of unique values;
- smooth stress scalar map;
- probability-density color ramps;
- high-cardinality animated quantitative colors.

Do not advertise current Blender backend as having arbitrary quantitative per-instance color attributes.

## Current Surface scalar-color capability

Current `Surface` Blender mapping receives:

```text
vertices
triangles
one primitive/material color
```

There is no source scalar attribute arriving from generic Scene.

Therefore continuous surface scientific colormaps require the future generic visual-attribute contract before Blender shader work can be scientifically correct.

See:

```text
VISUAL_ATTRIBUTE_MODEL.md
SCIENTIFIC_COLOR_POLICY.md
```

## Incremental geometry fast paths

Current `IncrementalBlenderBackend` has explicit in-place fast paths for:

```text
Point.position
PointCloud.positions
Polyline.points
Surface.vertices
VectorGlyphSet.origins/vectors
TextLabel.position
common transform/visibility changes
```

When topology/data structure remains compatible, native mesh/curve geometry can update in-place.

## Color changes are not current fast paths

This is an important premium-rendering constraint.

For `PointCloud`, the fast path accepts changes to:

```text
positions
```

while requiring other dataclass fields, including colors/radii/style, to remain equal.

For `VectorGlyphSet`, the fast path accepts changes to:

```text
origins
vectors
```

while colors must remain equal.

Therefore:

```text
animated position/vector values -> current in-place fast update
animated per-instance colors -> current fast path does not apply
```

## Fallback behavior for non-fast changes

When structure remains compatible but a primitive change cannot use a fast path, the incremental backend creates a temporary replacement primitive, assigns its new native data to the existing Blender object, then removes the temporary object and orphaned old datablock.

Consequence:

```text
Blender object identity can remain stable
but mesh/curve datablock identity may change
```

for style/color/unsupported mutations.

This distinction matters for premium acceptance tests.

Do not claim both object and datablock identity are preserved for every presentation change.

## Premium presentation identity target

For future quantitative attributes, preferred behavior should be:

```text
same Spectra primitive ID
same native object
same topology-compatible datablock
update scalar/color attribute buffer in-place
```

This should become a new fast path rather than replacing mesh/curve data every frame.

## Current TextLabel limitation

Text is native FONT geometry and receives body/size on creation.

Current incremental fast-path only recognizes position-only changes for TextLabel.

Therefore dynamically changing time-label text may currently trigger primitive data replacement rather than a tiny body-string update.

A premium presentation optimization should add an in-place text-body/size/color update path if profiling shows it matters.

This is small compared with dense field updates, but easy to improve later.

## Material update behavior

The incremental apply path reconstructs/ensures Scene material mappings each apply.

Presentation style changes should eventually avoid unnecessary scientific geometry replacement when only material parameters changed.

A dedicated material/style update path may be useful before frequent interactive preset switching is considered premium-ready.

## World/background support

Current Blender backend populates Spectra-owned collection/root and primitive resources, but generic Scene does not carry first-class world/background presentation semantics.

A future Blender premium adapter may control World/compositor state as presentation-owned backend state, but generic intent and ownership must be defined first.

## Geometry Nodes status

Current dense mapping does not use Geometry Nodes as the primary representation.

Potential future use:

```text
PointCloud instancing
VectorGlyph arrow instancing
per-instance scale/color attributes
LOD
```

But Geometry Nodes remains a backend optimization, not a scientific Scene contract.

## Capability-profile implications

When `BackendCapabilities` is later extended for presentation features, current source supports conservative claims such as:

```text
supports_world_space_text = true
supports_transparency = true
supports_materials = true
```

For the incremental backend, after fields are defined/validated:

```text
supports_incremental_geometry_updates = true
supports_topology_preserving_updates = true
```

Do not initially claim:

```text
supports_surface_vertex_attributes = true
supports_high_cardinality_per_instance_color = true
supports_instanced_glyphs = true
supports_volumetrics = true
supports_screen_space_labels = true
```

until corresponding runtime paths exist.

## Premium implementation priority from source audit

Highest-value Blender improvements after generic presentation/attribute semantics are green:

### B1 — presentation-owned camera/light/text/material application

Mostly existing primitives/backend mappings.

### B2 — material/style incremental updates

Avoid data replacement for preset/style-only changes where possible.

### B3 — scalar/per-instance attribute path

Replace bounded material-slot color strategy for quantitative data.

### B4 — dense Geometry Nodes/instanced glyph representation

Performance/visual quality improvement after correctness.

### B5 — world/background/compositor profile

Backend-specific premium effects after presentation ownership/capabilities are stable.

## Native acceptance implications

Future premium smoke should distinguish:

```text
scientific geometry animation:
  object identity stable
  datablock identity stable where fast path promises it

presentation style/color change:
  object identity should stay stable
  datablock identity may initially change unless attribute/style fast path exists

presentation-owned resource add/remove:
  scientific objects untouched
```

This makes the tests reflect actual guarantees instead of requiring impossible blanket identity behavior.

## Success criterion

Premium Blender work should build on existing verified batching and incremental geometry rather than rewrite it.

The biggest missing performance/quality path is a generic dense scalar/color attribute channel that Blender can update in-place and shade with a quantitative colormap.