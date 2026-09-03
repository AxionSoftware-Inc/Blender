# Spectra Science — BackendCapabilities Extension Plan

Status: **design plan, not implemented runtime**.

Current runtime already exposes one generic backend capability record:

```python
BackendCapabilities(
    primitive_kinds: frozenset[PrimitiveKind],
    supports_group_hierarchy: bool = True,
    supports_materials: bool = True,
)
```

This document defines how to extend that existing contract for premium presentation and visual attributes without creating a second renderer-capability system.

## Principle

`BackendCapabilities` remains the authoritative generic renderer feature profile.

Additive fields should:

- describe renderer-neutral behavior;
- have conservative defaults;
- not name Blender/WebGPU-native technologies;
- not claim features before they are validated;
- remain usable by MemoryBackend/future renderers.

## Proposed first additive fields

Conceptual future shape:

```python
@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    primitive_kinds: frozenset[PrimitiveKind]
    supports_group_hierarchy: bool = True
    supports_materials: bool = True

    supports_vertex_attributes: bool = False
    supports_instance_attributes: bool = False
    supports_incremental_attribute_updates: bool = False

    supports_transparency: bool = True
    supports_world_background: bool = False
    supports_post_processing: bool = False
    supports_volumetrics: bool = False
    supports_depth_of_field: bool = False
    supports_screen_space_labels: bool = False

    supports_incremental_geometry_updates: bool = False
    supports_topology_preserving_updates: bool = False
```

Do not add fields merely because one backend API happens to expose them.

## Dense representation hints

Performance recommendations should be separate from hard feature support where possible.

Possible optional fields later:

```text
recommended_max_glyphs
recommended_max_labels
recommended_max_points
```

These are hints, not scientific limits.

A backend may still support larger data with slower performance.

## Current Blender profiles

### BlenderBackend

Current source supports all current core primitive kinds and materials.

Conservative new-feature profile should initially remain:

```text
vertex attributes = false
instance attributes = false
incremental attribute updates = false
incremental geometry updates = false
```

Even if Blender itself has native attribute technology, Spectra's current mapping does not yet expose the generic contract.

### IncrementalBlenderBackend

Current source proves compatible in-place geometry updates for selected structures such as:

```text
PointCloud positions
Polyline points
Surface vertices
VectorGlyphSet origins/vectors
```

Therefore after validation an extended profile may advertise:

```text
supports_incremental_geometry_updates = true
supports_topology_preserving_updates = true
```

but **not** quantitative visual attribute updates until implemented.

## MemoryBackend

MemoryBackend is primarily semantic/testing storage.

It can represent any ordinary Scene value that Core supports, but it does not render advanced native effects.

Conservative presentation profile:

```text
post processing = false
volumetrics = false
depth of field = false
screen-space labels = false
```

If visual attributes are ordinary immutable Scene values, MemoryBackend may semantically retain them even though it does not render pixels. Distinguish semantic storage from rendering capability if needed.

## Hard vs soft semantics

Feature negotiation should classify requested features:

```text
required for scientific fidelity
preferred for visual quality
optional decoration
```

Examples:

### required

- quantitative per-vertex color when the selected view depends on it and no faithful fallback exists.

### preferred

- depth of field for cinematic preset.

### optional

- vignette/post-processing.

Unsupported required feature -> structured failure/fallback view request.

Unsupported preferred/optional feature -> deterministic degradation.

## Attribute fidelity

`supports_vertex_attributes=True` alone may be too weak if a backend stores attributes but cannot map them quantitatively to colors.

Potential later fields:

```text
supports_quantitative_color_mapping
supports_attribute_driven_scale
supports_attribute_driven_opacity
```

Add only when actual presentation contracts use them.

First visual-attribute checkpoint can simply require a backend adapter function that knows one explicit scalar-to-color binding and then decide whether another generic capability bit is justified.

## Dynamic/device capabilities

Static class-level `capabilities` works for current backends.

Future GPU/WebGPU/remote renderers may vary by device.

Do not break existing protocol prematurely.

Possible additive evolution later:

```python
def effective_capabilities(self) -> BackendCapabilities:
    return self.capabilities
```

or a separate optional introspection protocol.

Only introduce dynamic querying when a real backend requires it.

## Capability versioning

New boolean fields with conservative defaults are backward-friendly at source level.

Do not reinterpret an existing `True` field to mean a stronger capability later.

If semantics strengthen materially, add a new field or version the generic capability contract.

## Compatibility validation

Current `validate_backend_compatibility(scene, capabilities)` checks:

```text
primitive kinds
group hierarchy
materials
```

Future extension should not automatically reject every Scene containing attributes just because a backend cannot natively accelerate them.

Validation needs to distinguish:

```text
Scene can be represented semantically
presentation requires a specific feature
```

Preferred architecture:

- base Scene compatibility checks generic structural representation;
- presentation/backend resolution checks optional/required advanced features.

This prevents presentation quality constraints from polluting basic renderer compatibility.

## Renderer-private feature diagnostics

Backend-specific diagnostics may mention:

```text
Geometry Nodes unavailable
shader compile failed
GPU feature unsupported
```

but generic presentation policy sees normalized capability/fallback reasons.

Do not add fields such as:

```text
supports_geometry_nodes
supports_eevee
supports_cycles
```

to generic Core capability contracts.

## Test gate after implementation

- existing backend constructors work with new defaults;
- old tests using `BackendCapabilities(...)` remain source-compatible where possible;
- BlenderBackend advertises only implemented features;
- IncrementalBlenderBackend advanced booleans match validated behavior;
- required unsupported presentation feature fails deterministically;
- optional unsupported feature degrades;
- scientific Scene values unchanged by feature resolution;
- no backend-name `if` logic enters scientific domains.

## Success criterion

One additive generic capability record should be enough for current and future renderers to describe what they can faithfully/efficiently express, while scientific domains remain entirely unaware of Blender, WebGPU, Unreal, or any other renderer technology.
