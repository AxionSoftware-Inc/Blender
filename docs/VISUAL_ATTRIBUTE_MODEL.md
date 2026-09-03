# Spectra Science — Generic Visual Attribute Model

Status: **design contract; not implemented runtime**.

This document addresses the main generic visualization gap identified by `PRESENTATION_CORE_FEASIBILITY_AUDIT.md`: current `Surface` supports one uniform color, while premium scientific visualization often needs dense scalar/color data attached to vertices or instances.

## Why this matters

Several unrelated domains need the same capability:

```text
electrostatic potential slice
heat/temperature slice
stress field
CFD pressure/vorticity slice
quantum probability density
reaction-diffusion concentration
error/residual fields
```

A renderer-specific fix would repeat the same problem in Blender, WebGPU, and future backends.

The correct boundary is a renderer-neutral visual data channel.

## Current state

Current primitives already provide some dense styling:

```text
PointCloud.colors
PointCloud.radii
VectorGlyphSet.colors
```

Current `Surface` has:

```text
vertices
triangles
one uniform color
```

Scene schema is currently:

```text
spectra.scene v4
```

Any persistent primitive contract change therefore needs deliberate schema/version compatibility work.

## Design goals

A visual attribute model should:

- remain renderer-independent;
- support scalar/vector/color channels where genuinely useful;
- define attachment cardinality explicitly;
- distinguish scientific values from already-resolved colors;
- preserve stable topology/IDs for incremental backends;
- be serializable;
- support animation without rebuilding topology;
- work for Blender and WebGPU;
- avoid one bespoke field per scientific subject.

## Non-goals

Do not turn Scene into a general scientific database.

The attribute layer is for **visual representation data**, not the authoritative numerical solution.

The source solution/field remains owned by scientific semantics/result artifacts.

## Option A — add `Surface.colors`

Simplest extension:

```python
@dataclass(frozen=True)
class Surface:
    ...
    colors: tuple[Color, ...] = ()
```

Interpretation:

```text
empty -> uniform `color`
len(colors) == len(vertices) -> per-vertex colors
```

### Advantages

- simple;
- immediately useful;
- mirrors PointCloud/VectorGlyphSet style;
- easy backend mapping.

### Disadvantages

- only resolved RGBA survives;
- loses original scalar values/range semantics;
- legends need separate metadata;
- later scalar shader remapping requires recomputing colors;
- repeated pattern for future width/opacity/scalar attributes.

This is viable for a small product, but may be too narrow for Spectra's cross-renderer scientific goals.

## Option B — primitive-specific scalar channel

Example:

```python
@dataclass(frozen=True)
class Surface:
    ...
    scalar_values: tuple[float, ...] = ()
    scalar_attribute_name: str | None = None
```

### Advantages

- preserves quantitative values;
- renderer can map value -> color;
- legends can share same data/range.

### Disadvantages

- one scalar only;
- unclear unit/semantic metadata placement;
- surface-specific;
- future vector/multiple scalar channels lead to more fields.

Better scientifically than raw colors, but limited structurally.

## Option C — generic visual attribute channels

Recommended long-term direction.

Conceptual types:

```python
AttributeDomain = Literal[
    "vertex",
    "instance",
    "primitive",
]

AttributeValueKind = Literal[
    "scalar",
    "vec2",
    "vec3",
    "color",
]

@dataclass(frozen=True)
class VisualAttribute:
    name: str
    domain: AttributeDomain
    value_kind: AttributeValueKind
    values: tuple[object, ...]
```

A primitive can expose:

```python
attributes: tuple[VisualAttribute, ...] = ()
```

Possible examples:

```text
Surface:
  temperature@vertex : scalar
  resolved_color@vertex : color

PointCloud:
  concentration@instance : scalar
  species_color@instance : color

VectorGlyphSet:
  magnitude@instance : scalar
```

## Recommended separation: data vs presentation mapping

Prefer storing quantitative visual values separately from color mapping.

```text
VisualAttribute
  name = "temperature"
  domain = vertex
  value_kind = scalar
  values = (...)

Presentation color policy
  palette
  range
  clamp
  center
  unit/legend metadata
```

Then:

```text
scientific values
   ↓
presentation mapping
   ↓
backend shader / resolved colors
```

This preserves scientific interpretation across renderers.

## Where units belong

Do not duplicate the full Unit/Quantity model inside every attribute value.

A visual scalar attribute should reference presentation/semantic metadata such as:

```python
@dataclass(frozen=True)
class VisualAttributeMetadata:
    attribute_name: str
    quantity_name: str | None = None
    unit_symbol: str | None = None
    semantic_role: str | None = None
```

The exact location may be:

- presentation context;
- view semantic object;
- Scene-level visual metadata resource;

rather than primitive field itself.

The important requirement is that legends do not guess units.

## Cardinality validation

Attribute domains require strict counts.

For `Surface`:

```text
vertex domain -> len(values) == len(vertices)
primitive domain -> len(values) == 1
```

For `PointCloud`/`VectorGlyphSet`:

```text
instance domain -> len(values) == instance_count
```

Do not accept silent truncation or broadcasting except where explicitly defined.

## Animation

Attribute arrays should be animatable through the same stable-ID timeline model.

Conceptually:

```text
primitive.attributes["temperature"].values
```

However current property-path animation works best with dataclass fields and tuples.

Before implementation, evaluate whether generic keyed attribute paths require changing animation path resolution.

A lower-risk first runtime may add an explicit `Surface.scalar_values` field, prove animation/backend mapping, then generalize only if multiple attribute channels are immediately needed.

## Incremental backend implications

Blender/WebGPU should update dense attributes in-place when topology/cardinality is unchanged.

Preferred behavior:

```text
same primitive ID
same vertex/instance count
attribute values changed
    -> same native object/buffer
    -> update attribute buffer only
```

Structural change:

```text
attribute domain/count incompatible
    -> safe rebuild/fallback
```

Do not rebuild scientific geometry merely because scalar values changed.

## Blender mapping direction

Potential implementations:

```text
mesh color attribute
mesh float attribute + shader color ramp
Geometry Nodes named attribute
curve/spline attributes
```

The generic model must not expose these Blender names.

For quantitative surfaces, preserving scalar float attributes is preferable to baking colors when Blender can map them reliably.

## WebGPU mapping direction

Natural mapping:

```text
vertex/instance storage or vertex buffer
scalar attribute
uniform presentation range/palette
shader maps scalar -> color
```

This is another reason to preserve scalar values instead of only RGBA colors.

## Serialization options

Adding primitive attributes changes persistent Scene structure.

Preferred approach if generic attributes are adopted:

```text
spectra.scene v5
```

while keeping v1-v4 readers.

Example serialized form:

```json
{
  "kind": "surface",
  "vertices": [...],
  "triangles": [...],
  "attributes": [
    {
      "name": "temperature",
      "domain": "vertex",
      "value_kind": "scalar",
      "values": [300.0, 301.2, 303.7]
    }
  ]
}
```

Do not store presentation palette/range directly inside the scientific primitive unless that styling is intentionally part of the Scene presentation state.

## Backward compatibility

A v5 Surface without attributes behaves like v4.

When reading v1-v4:

```text
attributes = ()
```

When exporting to an older schema, dense attributes cannot be silently discarded if they carry required visual meaning. Either:

- reject downgrade;
- explicitly bake compatible colors where allowed and documented;
- export an alternate representation.

## Performance considerations

Large scalar arrays should remain tuples/contiguous buffers at semantic/runtime boundaries appropriate to current architecture.

For very large scenes, future Scene transport may reference external/chunked attribute buffers instead of embedding all values in JSON.

Do not solve large-array project storage inside the first attribute patch.

## Recommended implementation strategy

### Step A — do not change Core during Presentation Phase 1

Use existing uniform/per-instance colors only.

### Step B — collect exact requirements from first scalar premium scenes

Minimum proofs:

```text
electrostatic potential Surface
thermoelastic temperature/stress Surface
quantum probability Surface
```

### Step C — choose between minimal scalar field and generic attributes

Given current architecture breadth, the preferred target is a generic attribute model **if** animation/property-path/backend implementation remains tractable.

If generic animation would force a large cross-cutting refactor, implement a narrower `Surface.scalar_values` proof first in its own checkpoint.

### Step D — version Scene schema deliberately

Do not combine:

```text
presentation composer
+ attribute model
+ Scene v5
+ Blender shader mapping
```

into one unchecked package.

Recommended packages:

```text
W3a: generic/Surface scalar attribute semantics + serialization/tests
W3b: presentation range/legend mapping
W3c: Blender attribute/shader interpretation
```

## Required tests when implemented

- cardinality validation;
- duplicate attribute names rejected;
- non-finite scalar behavior explicitly defined;
- v1-v4 read compatibility;
- v5 round-trip;
- timeline updates preserve primitive identity;
- MemoryBackend sees attributes;
- Blender attribute update preserves mesh object/datablock identity;
- scalar values map to same legend range;
- quantitative values are not silently altered by renderer.

## Success criterion

A temperature/potential/stress/probability scalar field should be able to travel through:

```text
scientific result
  -> explicit view sampling
  -> generic dense visual scalar attribute
  -> presentation color policy + legend
  -> Blender/WebGPU shader mapping
```

without copying domain-specific scalar arrays into renderer code and without turning every sampled value into a separate Scene object.