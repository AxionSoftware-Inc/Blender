# Spectra Science — Scene v5 Visual Attribute Migration Plan

Status: **design migration plan, not implemented runtime**.

Current persistent Scene schema is `spectra.scene` version 4 with reader compatibility for v1–v4.

This document defines a conservative path if generic visual attributes become persistent Scene data and require a future v5.

## Trigger

Do not bump Scene schema merely because presentation value objects exist.

A v5 is justified only when persistent `Scene` itself gains a new semantic field/resource that v4 cannot represent, for example generic visual attributes attached to primitives.

## Candidate v5 change

Potential additive field:

```text
primitive.attributes
```

containing renderer-neutral named channels such as:

```text
temperature scalar per vertex
von_mises scalar per vertex/instance
probability_density scalar
phase scalar cyclic metadata via quantity ID
```

The exact runtime API must be validated before freezing the serialization shape.

## Compatibility target

Reader behavior after v5 implementation:

```text
SUPPORTED_SCENE_SCHEMA_VERSIONS = {1, 2, 3, 4, 5}
```

v1–v4 scenes decode with:

```text
attributes = empty/default
```

so old files retain existing behavior.

A v5 writer should always emit explicit schema/version.

## Why additive default is preferable

If `attributes` defaults empty, old semantic behavior remains representable.

This avoids forcing migration code to synthesize scientific channels that did not exist in historical files.

Legacy fields such as `PointCloud.colors` remain authoritative for old scenes.

## Attribute serialization shape

Conceptual only:

```json
{
  "name": "temperature",
  "association": "vertex",
  "kind": "scalar",
  "quantity_id": "physics.temperature",
  "unit": {
    "name": "kelvin",
    "symbol": "K",
    "dimension": {"temperature": 1},
    "scale_to_si": 1.0,
    "offset_to_si": 0.0
  },
  "values": [300.0, 301.5, 305.2]
}
```

Do not serialize backend-native buffer handles, Blender attribute names, shader node IDs, or GPU pointers.

## Unit encoding reuse

Experiment artifact serialization already contains explicit Unit/Dimension encoding patterns.

Before implementing Scene v5, consider extracting/reusing a common internal unit codec rather than creating another subtly different unit JSON format.

However, do not refactor serialization infrastructure solely for aesthetic deduplication unless tests make the change safe.

## Legacy color fields

v5 does not immediately remove:

```text
PointCloud.colors
VectorGlyphSet.colors
Surface.color
```

Rules:

- old fields keep old meaning;
- new attributes are additive;
- explicit presentation binding determines when an attribute drives displayed color;
- no ambiguous automatic override.

A later schema may deprecate redundant fields only after a stable migration path exists.

## Validation on decode

After reading attribute payloads, normal runtime constructors validate:

- attribute name;
- kind;
- association;
- finite values;
- count matches primitive geometry;
- unit/quantity metadata.

Malformed v5 data should raise `SceneSerializationError` or a structured wrapper; it must not partially create invalid Scene objects.

## Large-array concern

JSON is not ideal for very large scalar channels.

Scene v5 should not attempt to solve project-scale external storage simultaneously.

Initial contract can support normal/small Scene attributes in JSON.

Large project/result arrays remain candidates for project artifact/chunked storage, with visualization Scene materialized at runtime.

Do not put file paths or lazy external array handles into generic Scene v5 without a separate resource contract.

## Timeline interaction

Visual attributes may vary over time, but v5 should not automatically introduce giant tuple keyframes.

Preferred first model:

```text
Scene.sample(t) produces a static Scene snapshot with current attributes
BackendSession applies snapshot
incremental backend updates compatible native attribute buffer
```

Existing Timeline remains suitable for ordinary scalar/dataclass properties.

A specialized large-buffer animation contract can be added later if profiling justifies it.

## Backend compatibility

MemoryBackend should preserve/inspect attributes once Core supports them.

Blender/WebGPU adapters may initially support only subsets.

Scene decode must not depend on a renderer being present.

Presentation/backend feature negotiation decides whether a requested attribute mapping can be faithfully displayed.

## Migration fixtures

Before merging v5, preserve fixtures for:

```text
v1 minimal Scene
v2 fixture
v3 fixture
v4 current Scene with materials/camera/light/timeline
v5 static Surface scalar attribute
v5 PointCloud instance attribute
```

Tests should prove old fixtures load to semantically equivalent current `Scene` values.

## Round-trip tests

Required:

- v5 scalar attribute round-trip;
- Vec2/Vec3/Color attribute kind round-trip if supported;
- units preserved;
- quantity ID preserved;
- deterministic JSON ordering;
- malformed kind fails;
- malformed association fails;
- wrong element count fails;
- non-finite value fails;
- empty/default attributes behave exactly like v4 semantics.

## Schema bump procedure

Recommended work-package sequence:

1. implement runtime VisualAttribute contracts without serialization if possible;
2. prove in-memory Scene behavior;
3. choose primitive integration model;
4. update serializer writer/reader;
5. bump `SCENE_SCHEMA_VERSION = 5`;
6. add 5 to supported versions;
7. add legacy fixtures/tests;
8. add v5 round-trip tests;
9. update docs and project/export compatibility notes;
10. only then begin native Blender/WebGPU attribute persistence assumptions.

## Rollback strategy

Because schema change is isolated, if implementation proves flawed before release:

- revert the runtime/schema work package;
- Phase 1 premium camera/light/title functionality remains on v4;
- no need to revert scientific domains or numerical execution.

This is why visual attributes are intentionally a separate checkpoint after the generic presentation composer.

## Project interaction

A future `spectra.project` may store authoritative result arrays outside Scene JSON and regenerate Scene v5 attributes on demand.

Therefore Scene v5 attributes should be treated as renderer-neutral visualization state, not necessarily the sole durable scientific result storage.

## Success criterion

Scene v5, if introduced, should add one clean renderer-independent ability—named visual data channels—while preserving v1–v4 readability, existing primitive behavior, renderer independence, and separation between scientific result storage and visualization/rendering caches.
