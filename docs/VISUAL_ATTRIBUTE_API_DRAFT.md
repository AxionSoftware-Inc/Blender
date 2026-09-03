# Spectra Science — Visual Attribute Runtime API Draft

Status: **design draft, not implemented runtime**.

This document turns the visual-attribute concept into a concrete renderer-neutral API shape for a later isolated runtime checkpoint.

The need is established by current source:

- `Surface` carries one primitive-level color only;
- `PointCloud` and `VectorGlyphSet` carry per-instance color tuples but no named generic scalar channels;
- current Blender high-cardinality colors are material-slot based and bounded;
- incremental geometry paths do not provide an equivalent generic animated attribute update path.

## Goal

Allow scientific visualization compilers to attach explicit numeric/color data channels to generic visual geometry without embedding Blender/WebGPU shader logic or domain-specific fields into Core primitives.

Conceptual flow:

```text
scientific semantic view
    -> geometry + named visual attribute channels
    -> resolved color/size/etc presentation policy
    -> Scene
    -> backend native attribute buffers/shaders
```

## Design principles

1. attributes are visualization data, not solver storage;
2. renderer-neutral names/semantics;
3. explicit association/domain (vertex/instance/etc.);
4. immutable Core values;
5. length/shape validation;
6. serialization/versioning deliberate;
7. animation/value updates can preserve geometry identity;
8. backends may choose native buffer representation;
9. scientific values/ranges remain engine-owned;
10. no arbitrary renderer shader dictionaries.

## Association

Initial vocabulary:

```python
VisualAttributeAssociation = Literal[
    "vertex",
    "instance",
    "primitive",
]
```

Potential later associations:

```text
face
corner
segment
voxel/cell
```

Do not add them until real views require them.

## Value kind

Initial generic kinds:

```python
VisualAttributeKind = Literal[
    "scalar",
    "vec2",
    "vec3",
    "color",
]
```

This covers most immediate presentation needs.

Avoid generic `object` payloads.

## VisualAttribute

Conceptual immutable contract:

```python
@dataclass(frozen=True, slots=True)
class VisualAttribute:
    name: str
    association: VisualAttributeAssociation
    kind: VisualAttributeKind
    values: tuple[float | Vec2 | Vec3 | Color, ...]
    quantity_id: str | None = None
    unit: Unit | None = None
```

Validation:

- non-empty stable `name`;
- values non-empty unless primitive semantics explicitly permit empty geometry;
- all values match declared `kind`;
- scalar values finite;
- vector components finite;
- `unit` meaningful mainly for numeric scientific channels, not RGBA colors;
- `quantity_id` is semantic identity, not display label.

## Why named scalar values rather than only colors

For quantitative scientific data, storing only colors loses information needed for:

- changing palette without recompiling science;
- changing display range;
- generating legends;
- accessibility/preset changes;
- backend-native palette evaluation;
- inspection/export.

Preferred scientific view output:

```text
attribute name = temperature
kind = scalar
unit = K
values = (...)
```

Presentation then resolves range/palette.

A precomputed `color` channel is still valid for categorical/decorative data or a fully resolved display cache.

## AttributeSet

Conceptual reusable container:

```python
@dataclass(frozen=True, slots=True)
class VisualAttributeSet:
    attributes: tuple[VisualAttribute, ...] = ()

    def get(self, name: str) -> VisualAttribute: ...
```

Rules:

- unique names within one set;
- deterministic ordering by name or declaration contract;
- immutable.

## Primitive integration options

### Option A — common Primitive field

```python
@dataclass(frozen=True)
class Primitive:
    ...
    attributes: VisualAttributeSet = VisualAttributeSet()
```

Pros:

- uniform across primitive types;
- future attributes can reach Polyline/Region/etc.

Cons:

- changes every primitive equality/serialization contract;
- association validation depends on concrete primitive type.

### Option B — only dense primitives initially

Add attributes to:

```text
Surface
PointCloud
VectorGlyphSet
```

Pros:

- smaller schema/runtime change;
- immediate known use cases.

Cons:

- less uniform;
- later migration if Polyline/others need channels.

### Recommendation

Prefer a common `Primitive.attributes` field **only if** schema/equality/backend impact is accepted in an isolated checkpoint and concrete association validators remain centralized.

Otherwise use dense-primitives-first v1, then promote after evidence.

Do not implement the field as an untyped `dict[str, tuple]`.

## Association length validation

Concrete primitive expectations:

### Surface

```text
vertex -> len(vertices)
primitive -> 1
```

Future face association:

```text
face -> len(triangles)
```

### PointCloud

```text
instance -> len(positions)
primitive -> 1
```

### VectorGlyphSet

```text
instance -> len(origins) == len(vectors)
primitive -> 1
```

### Polyline later

Potential:

```text
vertex -> len(points)
segment -> len(points)-1 (or closed semantics)
```

Do not guess segment semantics in first version.

## Existing color fields

Current primitives already have fields such as:

```text
Surface.color
PointCloud.color/colors
VectorGlyphSet.color/colors
```

Backward compatibility strategy:

- existing fields remain valid;
- visual attributes are additive;
- presentation/backend chooses explicit attribute mapping only when requested;
- no implicit precedence ambiguity.

For example:

```text
no color attribute/policy -> existing primitive color behavior
resolved quantitative color attribute -> backend uses resolved mapping
```

A future deprecation of legacy per-instance colors should occur only after attribute path proves stable.

## Presentation binding

Do not force palette/range into the attribute itself.

Conceptual binding:

```python
@dataclass(frozen=True)
class AttributePresentationBinding:
    primitive_id: str
    attribute_name: str
    channel: str                # color | scale | opacity | etc.
    color_scale: ResolvedColorScale | None = None
```

The binding belongs to resolved presentation/view state, not raw scientific attribute data.

For initial implementation, only `channel="color"` may be supported.

## Color rendering paths

Backend can realize the same scalar/color semantics through either:

### precomputed color buffer

```text
scalar values + ResolvedColorScale
-> Spectra computes Color tuple
-> backend uploads colors
```

### scalar native attribute + backend palette

```text
scalar/normalized values
-> backend native attribute
-> backend shader palette evaluation
```

The resolved numeric range/palette remains Spectra-owned in both cases.

Parity tests should compare representative outputs.

## Incremental update

Attribute values should be separately updateable from geometry structure.

Conceptual change classes:

```text
geometry stable + attribute values changed -> attribute fast update
attribute schema changed -> attribute buffer rebuild
geometry topology changed -> normal structural fallback
```

For animated temperature/stress/phase:

```text
same Surface vertices/triangles
same attribute name/association/kind/count
new scalar values
```

should ideally preserve native object/mesh identity and update one native attribute buffer.

## Backend capability extension

Existing `BackendCapabilities` should eventually gain conservative generic features such as:

```text
supports_instance_attributes
supports_vertex_attributes
supports_quantitative_color_mapping
supports_incremental_attribute_updates
```

Do not expose Blender Geometry Nodes names in generic capability fields.

A backend lacking required quantitative attribute support may:

- accept a Spectra-precomputed color fallback if faithful;
- use explicit coarse fallback if user/policy allows;
- fail required-quality presentation.

Never silently discard the attribute.

## Blender mapping target

Future Blender path should prefer native data attributes rather than hundreds of materials.

Conceptual:

```text
Surface vertex scalar
-> Mesh attribute / color attribute
-> Spectra-managed material/node group
-> palette mapping
```

For PointCloud/VectorGlyphSet premium representations:

```text
instance scalar/color/scale
-> Geometry Nodes/native attributes
-> one/few batched objects
```

Exact node names remain backend-private.

## WebGPU mapping target

Conceptual:

```text
VisualAttribute.values
-> typed GPU vertex/storage buffer
-> shader input
```

Same quantity/range/palette semantics.

This validates why the Core contract must not be Blender-specific.

## Serialization

If visual attributes become part of persistent `Scene`, this is a Scene schema change from current v4.

Follow `SCENE_SCHEMA_EVOLUTION_CHECKLIST.md`.

Potential serialized shape:

```json
{
  "name": "temperature",
  "association": "vertex",
  "kind": "scalar",
  "quantity_id": "physics.temperature",
  "unit": {"...": "..."},
  "values": [300.0, 301.2, 305.0]
}
```

Large attributes make JSON inefficient, but current Scene serializer is JSON-oriented. For first semantic contract tests small arrays are acceptable; project/artifact storage may later externalize large buffers.

Do not prematurely put process/GPU buffer handles into serialized Scene.

## Timeline animation

Naively animating a huge attribute tuple through existing generic `Track` may be memory-heavy.

Possible initial approach:

- semantic time-dependent view/compiler creates sampled Scene snapshots as it already does for changing geometry;
- `BackendSession.seek()` receives each static Scene snapshot;
- incremental backend detects same attribute schema and updates values.

This avoids introducing a new giant-array Timeline interpolation contract immediately.

Later buffer-track abstractions can be justified by profiling.

## Quantity/unit ownership

The attribute may carry `quantity_id` and `unit` because these describe the numeric channel itself.

Presentation decides display unit/range/palette.

Example:

```text
attribute unit = K
presentation display unit = °C (if supported through explicit unit conversion)
```

Backend receives already-resolved display semantics or scalar values with enough metadata; it does not decide units.

## Initial cross-domain proof cases

### Heat

```text
Surface vertex attribute: temperature [K]
```

### Elasticity

```text
Surface/PointCloud attribute: von_mises_stress [Pa]
```

### Quantum

```text
probability_density scalar
phase scalar cyclic
```

### CFD

```text
pressure / speed / vorticity scalar slice
```

### Maxwell

```text
VectorGlyphSet instance attribute: |E| or |B|
```

These demonstrate the abstraction is not subject-specific.

## First implementation checkpoint

Do not combine with Phase 1 presentation semantics.

After Phase 1 generic composer is green:

1. add immutable attribute value contracts;
2. integrate into selected primitive(s);
3. validate association/count rules;
4. update Scene serialization/version deliberately;
5. MemoryBackend/Scene tests;
6. one static temperature Surface attribute;
7. generic color normalization/binding;
8. Blender static attribute mapping;
9. incremental animated attribute update;
10. then quantum/CFD/premium showcase expansion.

## Tests after implementation gate

- duplicate attribute names rejected;
- wrong kind rejected;
- non-finite scalar rejected;
- wrong association count rejected;
- old primitives without attributes behave unchanged;
- old Scene schema fixtures still read according to migration policy;
- new schema round-trip preserves attributes/units;
- presentation palette changes without scientific attribute mutation;
- same geometry + changed attribute preserves generic scientific primitive ID;
- Blender attribute value update preserves native object/mesh identity when compatible;
- backend quantitative color matches legend range;
- WebGPU/future backend can consume same generic contract without scientific-domain changes.

## Success criterion

Temperature, stress, probability density, phase, velocity magnitude, electric-field magnitude, and other quantities should all travel through one generic visualization-data path:

```text
scientific quantity -> named visual attribute -> explicit presentation mapping -> renderer-native buffer/shader
```

without adding subject-specific fields to `Surface`, reconstructing science inside Blender, or creating one native object/material per sample.
