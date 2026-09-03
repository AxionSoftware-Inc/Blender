# Spectra Science — Blender Premium Implementation Blueprint

Status: **implementation blueprint; no Blender runtime changes in this docs-only phase**.

This document translates the premium presentation architecture into a file-level implementation sequence for the existing Blender backend.

## Current source layout

```text
spectra/backends/blender/
  __init__.py
  backend.py       static Scene -> Blender mapping
  incremental.py   stable-ID in-place/rebuild updates
  timeline.py      Blender frame/time transport
```

Premium Blender work should extend this stack, not create another Blender-only scientific scene system.

## Dependency order

Do not start Blender premium implementation until generic Premium Presentation Phase 1 is green in plain Python/MemoryBackend.

Required upstream first:

```text
PresentationIntent / resolved policy
presentation composer
camera fit
presentation deterministic IDs
animation conflict rules
```

Visual attributes/Scene v5 are a later independent checkpoint for quantitative dense colors.

## B0 — no-op verification checkpoint

Before editing Blender backend after the next runtime validation:

- rerun targeted current native baseline if backend work is about to begin;
- confirm PointCloud/Polyline/Surface/VectorGlyphSet incremental identity paths still pass;
- record Blender version.

Do not combine historical backend regression fixes with premium feature implementation if avoidable.

## B1 — generic composed Scene through existing backend

No backend feature changes required initially.

Take a generic presentation-composed Scene containing only current primitives:

```text
Camera
Light
TextLabel
Polyline/Surface/PointCloud/etc.
```

Feed through:

```python
BackendSession.open(IncrementalBlenderBackend(), composed_scene)
```

Verify current mapping already renders:

- presentation camera;
- presentation lights;
- title/annotation text;
- axes built from Polyline/TextLabel;
- scientific geometry.

This checkpoint proves Premium Phase 1 can improve Blender output without backend schema changes.

## B2 — ownership metadata

Current backend owns resources through its dedicated collection/handle tables. Premium product usage needs stronger inspectable ownership.

Add backend-private metadata where safe, conceptually:

```text
spectra.semantic_id
spectra.owner/session token
spectra.resource_kind = scientific | presentation
```

Likely edit locations:

```text
backend.py::_create_primitive
incremental.py::_populate_incremental / replacement path
```

Rules:

- metadata mirrors generic Scene ID; it is not new scientific identity;
- cleanup still relies on owned handle/collection, not arbitrary name matching;
- user Blender content never removed because of a similar name.

Native metadata API names remain backend implementation details.

## B3 — presentation camera/light incremental updates

Current `IncrementalBlenderBackend` preserves compatible primitives but some property changes may fall back to data replacement.

Add/verify focused fast paths for presentation-heavy changes:

```text
Camera transform
Camera projection/FOV/ortho scale/clip values
Light transform
Light color/intensity/range/spot angle
TextLabel text/size/color/position where structurally compatible
```

Goal:

- camera motion/preset adjustments do not rebuild scientific geometry;
- time labels can update without replacing the entire Scene;
- light rig tweaks preserve object identity.

Suggested helper organization in `incremental.py`:

```text
_fast_update_camera
_fast_update_light
_fast_update_text
```

Keep `_replace_native_primitive` as safe fallback.

## B4 — material/style updates

Current `_create_material` maps generic Material to Blender nodes.

Premium rules:

- quantitative unlit material remains color-faithful;
- context lit materials use generic roughness/metallic/emission only;
- presentation preset does not pass Eevee/Cycles/node option dictionaries through Core.

Add in-place material update helper before creating new datablocks repeatedly.

Conceptually:

```text
same Spectra material ID + compatible material type
    -> update existing native material nodes/values
```

Track Spectra-owned material identity deterministically.

Required regression:

```text
repeated Scene apply with same material IDs
-> material count stable
```

## B5 — world/background adapter

Only after a generic environment/background presentation contract exists or backend-resolved presentation explicitly owns backend environment state.

Do not modify Scene v4 merely inside Blender backend to infer `dark_lab` background from label colors.

When implemented:

- world/background is Spectra presentation-owned backend state;
- previous non-Spectra world state should be restorable/preserved according to session policy;
- analysis/publication can request neutral/transparent output;
- cinematic/dark_lab can request dark environment.

Keep exact World node topology backend-private.

## B6 — visual attributes foundation

Prerequisites:

```text
VisualAttribute runtime contract
Scene v5 serialization/migration if persisted
BackendCapabilities additive extension
plain-Python attribute tests green
```

Then add Blender mapping.

### Surface vertex scalar/color

Preferred direction:

```text
Surface vertices + visual attribute
  -> Blender mesh named attribute/color attribute
  -> one material/shader evaluates color policy
```

Do not split Surface into thousands of objects/materials.

### PointCloud instance scalar/color

Replace high-cardinality material-slot path with attribute-driven mapping where possible.

### VectorGlyphSet instance scalar/color

Likewise use scalable curve/instance attributes rather than one material slot per unique continuous value.

Current <=256 material-slot path can remain fallback for small categorical/discrete colors until new path is validated.

## B7 — incremental attribute updates

Current source has fast geometry paths for:

```text
PointCloud.positions
Surface.vertices
VectorGlyphSet origins/vectors
```

but changing colors/attributes does not have an equivalent generic fast path.

Add topology-compatible attribute update methods:

```text
_fast_update_point_cloud_attributes
_fast_update_surface_attributes
_fast_update_vector_glyph_set_attributes
```

Requirements:

- same native object identity;
- same mesh/curve datablock when representation compatible;
- no material-count growth;
- value-buffer update only;
- animation sampling drives updates through normal BackendSession/Scene.sample path.

## B8 — Geometry Nodes dense presentation

Only after attribute mapping is correct.

Candidate uses:

- instanced sphere/point marker rendering;
- arrow instancing;
- per-instance scale/color;
- display-only LOD.

Recommended backend-private modules when complexity grows:

```text
spectra/backends/blender/presentation.py
spectra/backends/blender/attributes.py
spectra/backends/blender/geometry_nodes.py
```

Do not let node group names/types leak into `spectra.core` or scientific domains.

Node group ownership must be explicit and cleanup-safe.

## B9 — compositor/post effects

Late premium checkpoint.

Only cinematic/high output modes should opt in.

Possible backend-private effects:

```text
glare/bloom-like treatment
DOF
mist/depth cue
vignette
color management intent
motion blur
```

Rules:

- quantitative values understandable with effects disabled;
- analysis/publication conservative;
- user compositor content not destructively replaced without explicit session policy;
- effects are reproducible from presentation/backend settings.

## B10 — render/export presets

Separate rendering quality from scientific quality.

Conceptual backend output profiles:

```text
interactive
preview
high
final
```

They may alter:

- sample counts;
- AA;
- render resolution/output;
- expensive effects.

They must not alter:

- solver precision;
- field values;
- scientific timeline;
- quantitative range.

## Existing functions to preserve

`backend.py` source already centralizes:

```text
_require_blender
_populate_scene
_create_primitive
_create_point_cloud
_create_surface
_create_vector_glyph_set
_create_text
_create_camera
_create_light
_create_material
_remove_owned_scene
```

Prefer extracting helpers when necessary rather than duplicating mappings in a new premium backend.

`incremental.py` already owns:

```text
structure compatibility
common property updates
PointCloud/Polyline/Surface/VectorGlyphSet geometry fast paths
native primitive replacement fallback
```

Premium incremental work belongs here or in small imported backend-private helpers.

## BackendCapabilities

Extend existing `BackendCapabilities` additively after the dedicated capability checkpoint.

Potential validated Blender flags later:

```text
incremental_geometry_updates
per_instance_color
surface_vertex_attributes
point_cloud_attributes
instanced_glyphs
world_background
post_processing
```

Do not mark a capability true because Blender itself can theoretically do it. Mark it true only when this Spectra backend path implements and validates it.

## Presentation application model

Preferred product flow remains:

```text
scientific semantic object
 -> VisualizationRegistry.compile
 -> base Scene
 -> compose_presentation
 -> enriched Scene
 -> BackendSession.open(IncrementalBlenderBackend, scene)
 -> seek(t)
```

No Blender adapter should compile scientific semantic objects itself.

## Canonical native scenes

Implementation should be promoted against:

1. Maxwell E/B vectors;
2. Electrostatic field laboratory;
3. Quantum probability/phase;
4. Thermoelastic deformation;
5. Schwarzschild geodesics.

Use `PREMIUM_SHOWCASE_ACCEPTANCE_DATA.md` for required scientific/presentation assertions.

## Native regression gates

For every major Blender premium checkpoint:

- stable Spectra primitive ID -> stable Blender object where compatible;
- geometry/material/attribute datablock identity stable where fast path promises it;
- object count stable over animation;
- material count stable;
- no orphan growth;
- cleanup removes Spectra-owned resources only;
- preset switching does not duplicate cameras/lights/labels;
- scientific geometry remains identical under presentation-only changes;
- Scene sampling remains engine-owned.

## Performance gates

Measure separately:

```text
first create
value-only apply
camera/light/text-only apply
geometry apply
attribute-only apply
structural preset change
```

Do not quote one aggregate frame time without saying which category changed.

Dense target behavior:

```text
one PointCloud -> O(1) Blender objects
one VectorGlyphSet -> O(1) Blender objects
one quantitative Surface -> O(1) Blender mesh object
```

Native internal vertex/spline counts scale with data; Blender object counts must not scale linearly with samples.

## Save/reload gate

Before calling Blender presentation beta-quality:

- save `.blend` with a Spectra-generated scene;
- reload;
- ownership/semantic IDs remain inspectable where intentionally persisted;
- reconnect/rebuild from Spectra project/Scene is deterministic;
- `.blend` is still not the scientific source of truth.

## Suggested work packages

```text
BP1: composed Scene native smoke
BP2: ownership metadata
BP3: camera/light/text incremental updates
BP4: material lifecycle/update
BP5: environment/background
BP6: visual attributes static
BP7: visual attributes animated/incremental
BP8: Geometry Nodes dense instancing
BP9: optional compositor/render output
BP10: full premium acceptance suite
```

Each package should finish green before the next materially changes backend representation.

## Exit criterion

Blender premium work succeeds when a presentation-composed scientific Scene looks intentionally authored while remaining:

- reproducible;
- renderer-neutral upstream;
- scientifically faithful;
- incremental;
- dense-data scalable;
- cleanup-safe;
- replaceable by another backend without changing physics/math/domain code.