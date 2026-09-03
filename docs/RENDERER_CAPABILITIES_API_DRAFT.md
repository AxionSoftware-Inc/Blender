# Spectra Science — Backend Capability Negotiation API Draft

Status: **design draft, not implemented runtime**.

This document defines how premium presentation should adapt to Blender, WebGPU, MemoryBackend, headless renderers, or future backends without creating a second capability system.

## Important source-of-truth correction

Spectra already has:

```python
spectra.backends.base.BackendCapabilities
```

with current fields:

```text
primitive_kinds
supports_group_hierarchy
supports_materials
```

and every backend exposes a class-level:

```python
capabilities: BackendCapabilities
```

Therefore premium presentation must **extend the existing `BackendCapabilities` contract**, not introduce a parallel `RendererCapabilities` record.

This avoids two conflicting answers to the question:

> What can this backend represent?

## Goal

Target flow:

```text
base Scene
+ PresentationIntent
+ existing BackendCapabilities
        ↓
backend-aware presentation resolution
        ↓
resolved presentation plan + explicit fallbacks
        ↓
backend
```

Scientific domains remain unaware of backend identity.

## Proposed additive `BackendCapabilities` fields

Potential future extension:

```python
@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    primitive_kinds: frozenset[PrimitiveKind]
    supports_group_hierarchy: bool = True
    supports_materials: bool = True

    # presentation/data features — additive, conservative defaults
    supports_per_instance_color: bool = False
    supports_per_instance_scale: bool = False
    supports_instanced_glyphs: bool = False
    supports_point_cloud_attributes: bool = False
    supports_surface_vertex_attributes: bool = False

    supports_transparency: bool = False
    supports_volumetrics: bool = False
    supports_post_processing: bool = False
    supports_depth_of_field: bool = False
    supports_world_background: bool = False
    supports_screen_space_labels: bool = False
    supports_world_space_text: bool = True

    supports_incremental_geometry_updates: bool = False
    supports_topology_preserving_updates: bool = False

    max_recommended_glyphs: int | None = None
    max_recommended_labels: int | None = None
```

Exact field names are provisional until implementation.

Rules:

- new fields get conservative defaults;
- existing backends remain source-compatible where possible;
- do not encode native technology names such as Geometry Nodes, Eevee, Cycles, Vulkan, or WebGPU shader features in the generic contract;
- backend-private diagnostics may expose those details separately.

## Existing Blender facts from source audit

Current `BlenderBackend` already declares support for all core primitive kinds plus materials/group hierarchy.

Current native mapping confirms:

```text
Camera -> Blender camera, perspective + orthographic
Light -> Blender native light
TextLabel -> Blender FONT curve
Material -> node material
PointCloud -> one mesh object
VectorGlyphSet -> one multi-spline Curve object
```

Current batched color path:

```text
PointCloud.colors
VectorGlyphSet.colors
```

is implemented through Blender material slots, with an explicit guard of at most **256 unique colors per batched primitive**.

Therefore current Blender behavior is best described as:

```text
supports bounded per-instance categorical/resolved colors
```

not yet:

```text
supports arbitrary high-cardinality quantitative per-instance attributes
```

A future attribute/shader path should replace that bounded material-slot fallback.

## Current Surface limitation

Current Blender `Surface` mapping creates a mesh from vertices/triangles and applies one primitive/material color.

There is no generic Surface vertex scalar/color attribute in current Core/Scene schema.

Therefore do not advertise:

```text
supports_surface_vertex_attributes = true
```

until both:

1. generic Scene attribute semantics exist;
2. Blender mapping is implemented and validated.

See `VISUAL_ATTRIBUTE_MODEL.md`.

## Incremental backend facts

The separately verified `IncrementalBlenderBackend` preserves stable object/datablock identity for common topology-stable updates.

A future capability field can state this generically, but it should be attached to the actual incremental backend profile rather than the conservative rebuild-oriented `BlenderBackend` profile.

Distinguish:

```text
backend can render primitive
backend can update primitive interactively
backend can update native geometry in-place
```

These are not the same guarantee.

## Presentation resolution types

Suggested additive types outside backend Core:

```python
@dataclass(frozen=True)
class PresentationFallback:
    feature: str
    requested: str
    resolved: str
    reason: str

@dataclass(frozen=True)
class BackendResolvedPresentation:
    presentation: ResolvedPresentation
    fallbacks: tuple[PresentationFallback, ...] = ()
```

Suggested pure function:

```python
def resolve_presentation_for_backend(
    presentation: ResolvedPresentation,
    capabilities: BackendCapabilities,
) -> BackendResolvedPresentation:
    ...
```

No backend SDK import is needed for this resolution.

## Hard vs soft presentation requirements

```python
class PresentationRequirementLevel(str, Enum):
    PREFERRED = "preferred"
    REQUIRED = "required"
```

Example:

```text
preferred depth of field
required quantitative scalar color fidelity
```

If a required capability cannot be represented, return/fail with a structured diagnostic rather than silently changing scientific meaning.

## Fallback examples

### Depth of field

Unsupported:

```text
resolve to no DOF
```

Safe because aesthetics change, science does not.

### Screen-space legend

Unsupported but world-space text available:

```text
world-space TextLabel/legend composition
```

### Per-instance high-cardinality scalar color

If backend only has bounded material slots:

Do **not** silently quantize a required continuous field into arbitrary material bins.

Allowed responses:

- choose another faithful representation;
- fail required-quality presentation;
- explicitly use an approximation policy if the user allows it.

### Volumetric view

If backend lacks volume support, do not invent an isosurface threshold.

Fallback is only valid when the semantic/view layer already supplies an explicit alternate view such as a slice or isosurface policy.

## Backend class API

Current backend contract uses a class attribute:

```python
class Backend(Protocol):
    name: str
    capabilities: BackendCapabilities
```

Keep this model for static backend capability profiles.

If device/runtime-specific capabilities later vary by GPU/device, add an explicit optional query method only when needed rather than replacing the existing static attribute immediately.

Conceptual later addition:

```python
def runtime_capabilities(self) -> BackendCapabilities:
    ...
```

but only if static metadata proves insufficient.

## Plugin renderer backends

Future backend plugins should provide normal backend classes/factories whose `capabilities` use the same existing contract.

Do not define a plugin-only renderer capability schema.

Conceptual descriptor:

```python
@dataclass(frozen=True)
class RendererBackendDescriptor:
    backend_id: str
    display_name: str
    factory: Callable[[], Backend]
```

The created backend supplies `BackendCapabilities` normally.

## Versioning

Because `BackendCapabilities` already exists, extend it carefully:

- additive fields with conservative defaults are preferred;
- do not reinterpret `supports_materials` to mean quantitative attributes;
- primitive support remains in `primitive_kinds`;
- new fields should describe orthogonal behavior.

Existing tests for `validate_backend_compatibility()` must remain valid.

## First implementation package

Do not extend `BackendCapabilities` during Presentation W1/W2 unless the composer actually needs negotiation.

Recommended order:

```text
W1/W2 generic presentation
    ↓
W3 quantitative/color needs become concrete
    ↓
add smallest necessary BackendCapabilities fields
    ↓
MemoryBackend + Blender profiles/tests
    ↓
backend-aware presentation fallback
```

This keeps the first presentation patch small.

## Tests when implemented

- old backend constructors/profiles remain valid with defaults;
- `BackendCapabilities.all_core_primitives()` still works;
- `validate_backend_compatibility()` behavior unchanged for primitive/material checks;
- MemoryBackend uses conservative presentation feature flags;
- Blender advertises only source-verified/validated features;
- IncrementalBlenderBackend advertises incremental guarantees separately;
- required unsupported presentation feature fails;
- preferred feature degrades deterministically;
- scientific Scene arrays are unchanged by negotiation;
- quantitative color never silently becomes decorative approximation.

## Success criterion

Spectra has **one backend capability contract**.

Scientific domains compile semantics into generic Scene/view data. Presentation consults `BackendCapabilities` to choose faithful presentation fallbacks. Blender/WebGPU details remain inside their adapters.