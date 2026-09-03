# Spectra Science — Scene Schema Evolution Checklist

Status: **source-audit/design contract; no runtime code changed**.

Current runtime uses:

```text
schema: spectra.scene
version: 4
supported read versions: 1, 2, 3, 4
```

The serializer explicitly encodes Scene frame, active camera, materials, primitives, and Timeline.

This document defines the gate for any future Scene-level schema change such as generic visual attributes or an environment/background resource.

## Why this matters

The premium-presentation audit identified likely future generic needs:

```text
continuous scalar/color attributes on Surface and dense primitives
generic presentation/environment/background intent
possibly reusable attribute buffers/resources
```

These should not be introduced as ad-hoc fields without considering persistence compatibility.

## Schema change classification

Before modifying Scene serialization, classify the change.

### Runtime-only, no Scene persistence impact

Examples:

```text
PresentationIntent stored in project runtime only
backend capability profile
temporary renderer cache
presentation planning diagnostics
```

Do not bump Scene schema.

### Backward-readable additive Scene field

Example:

```text
new optional primitive/resource field with deterministic default
```

May still require a schema bump if older readers must distinguish semantics explicitly.

Do not rely solely on Python default values as a compatibility policy.

### New semantic resource/type

Examples:

```text
AttributeBuffer
Environment resource
new primitive kind
```

Normally requires a deliberate schema version increment and fixtures.

### Semantic reinterpretation

Changing the meaning of an existing serialized field is strongly discouraged.

Prefer a new field/type/version rather than silently changing old meaning.

## Required review before version bump

For a proposed Scene v5 change answer:

1. Is the concept renderer-independent?
2. Is it used by at least multiple scientific/presentation domains?
3. Can it remain project/presentation metadata instead of Scene state?
4. Does it affect scientific meaning or display meaning only?
5. Is the new concept needed in MemoryBackend/headless inspection?
6. Can older Scene documents be upgraded deterministically?
7. Can the new serializer still read v1-v4 unchanged?
8. What is the behavior when a backend cannot represent the new feature?

If these questions are unclear, defer the schema change.

## Visual attribute candidate

The likely future generic attribute contract should be evaluated across at least:

```text
temperature
potential
stress
probability density
quantum phase
CFD scalar slices
PointCloud scalar values
VectorGlyphSet magnitude/color
```

A good contract should avoid separate one-off fields for every primitive whenever a reusable generic attribute model is justified.

Potential shape, not frozen:

```python
@dataclass(frozen=True)
class VisualAttribute:
    name: str
    domain: str      # vertex | instance | primitive | sample
    value_kind: str  # scalar | color | vector
    values: tuple[...]
    unit: Unit | None = None
```

The exact representation must also consider large-array storage/performance before becoming persistent Scene JSON.

## Do not put huge arrays blindly into Scene JSON

Current serializer emits tuples/lists directly into JSON.

For modest Scene geometry this is acceptable.

For future million-element attributes, persistent project/artifact storage may need chunked/binary resources rather than giant JSON arrays.

Therefore distinguish:

```text
in-memory Scene representation
portable small Scene JSON
large project/artifact storage
renderer execution buffers
```

They do not have to be the same physical format.

## Environment/background candidate

A generic environment resource should only enter Scene if Blender, WebGPU, headless/image export, and other backends share useful semantics such as:

```text
solid background color
transparent background intent
simple environment lighting intent
```

Do not expose Blender World nodes or compositor settings in Scene schema.

Advanced post-processing can remain backend/presentation policy.

## Version implementation checklist

If Scene v5 is approved:

```text
[ ] increment SCENE_SCHEMA_VERSION
[ ] add 5 to SUPPORTED_SCENE_SCHEMA_VERSIONS
[ ] preserve v1-v4 read behavior
[ ] explicit serializer path for new field/type
[ ] explicit deserializer defaults/migration
[ ] malformed new payload validation
[ ] unknown primitive/resource kind still fails clearly
[ ] round-trip tests
[ ] old-version fixture tests
[ ] deterministic JSON output tests
[ ] Scene.sample(t) still preserves new resources where appropriate
[ ] MemoryBackend compatibility
[ ] Blender/backend compatibility/fallback tests
[ ] docs/API stability update
```

## Migration fixtures

Keep small historical fixtures for each supported Scene schema version.

Minimum fixture classes:

```text
static primitive scene
animated scene
materials scene
camera/light scene
new v5 feature scene
```

A migration test should assert semantic equality after load, not textual equality with the original old JSON.

## Timeline compatibility

New animatable primitive/resource fields must explicitly decide whether Timeline property paths may target them.

If yes:

- type interpolation must be supported;
- Scene validation must accept the property path;
- serialization `_encode_value/_decode_value` must support keyframe values;
- animation ownership rules still apply.

Do not make a field animatable accidentally merely because it is a dataclass attribute.

## Backend compatibility

A new Scene semantic does not mean every backend must implement it immediately.

Extend `BackendCapabilities` conservatively and provide:

```text
faithful support
explicit deterministic fallback
or structured incompatibility
```

Never silently discard quantitative attributes.

## Project relationship

Presentation intent, solver policy, plugin requirements, model definitions, and experiment provenance belong primarily to project/artifact contracts, not Scene.

Scene should remain the renderer-neutral visual state needed to represent a compiled view at a given time.

This keeps Scene compact conceptually even as the product grows.

## Release gate

Do not remove old Scene reader versions in the same patch that introduces a new writer version.

Schema support retirement, if ever needed, is a separate compatibility decision under `API_STABILITY_POLICY.md` and `SCHEMA_VERSIONING_POLICY.md`.

## Success criterion

A future Scene schema change should be deliberate enough that a saved Spectra scene remains understandable years later, independent of whether it is rendered by Blender, WebGPU, or another backend.