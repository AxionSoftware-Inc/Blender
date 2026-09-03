# Spectra Science — Renderer Capability Negotiation API Draft

Status: **design draft, not implemented runtime**.

This document defines a concrete Python-facing contract for letting presentation logic adapt to Blender, WebGPU, headless, or future renderers without embedding renderer checks inside scientific domains.

## Goal

The presentation layer should be able to ask:

> What can this renderer express efficiently and faithfully?

and resolve deterministic presentation fallbacks while preserving scientific semantics.

Target flow:

```text
base Scene
+ PresentationIntent
+ RendererCapabilities
        ↓
resolved presentation plan
        ↓
renderer backend
```

The renderer capability profile is descriptive. It must not become the scientific model.

## Proposed capability record

```python
@dataclass(frozen=True)
class RendererCapabilities:
    backend_id: str
    backend_version: str | None = None

    per_instance_color: bool = False
    per_instance_scale: bool = False
    instanced_glyphs: bool = False
    point_cloud_attributes: bool = False
    surface_vertex_attributes: bool = False

    transparency: bool = True
    volumetrics: bool = False
    post_processing: bool = False
    depth_of_field: bool = False
    shadows: bool = True

    world_background: bool = True
    screen_space_labels: bool = False
    world_space_text: bool = True
    multiple_viewports: bool = False

    interactive_updates: bool = True
    incremental_geometry_updates: bool = False
    topology_preserving_updates: bool = False

    max_recommended_glyphs: int | None = None
    max_recommended_labels: int | None = None
```

Fields should represent generic rendering capabilities, not native API names.

Avoid:

```text
supports_geometry_nodes
supports_eevee_bloom
supports_cycles_ocio
```

Those may exist in backend-private diagnostics but should not define generic presentation semantics.

## Backend API

A backend may expose:

```python
class Backend(Protocol):
    def capabilities(self) -> RendererCapabilities:
        ...
```

For backward compatibility, a default conservative profile may be supplied by base backend infrastructure until all backends implement the method explicitly.

## Reference profiles

### MemoryBackend

Conceptually:

```text
backend_id = memory
interactive_updates = true
incremental_geometry_updates = false/semantic-only
world_space_text = representable as Scene content
post_processing = false
volumetrics = false
```

MemoryBackend exists for semantic inspection, not premium pixels.

### IncrementalBlenderBackend

Initial profile should describe only what current mapping actually supports reliably.

Conceptually:

```text
interactive_updates = true
incremental_geometry_updates = true
topology_preserving_updates = true
world_space_text = true
shadows = true
world_background = true
transparency = true
```

Do not mark `per_instance_color` or advanced instancing true until the native implementation is validated.

### Future WebGPU backend

Could eventually expose:

```text
per_instance_color = true
per_instance_scale = true
instanced_glyphs = true
point_cloud_attributes = true
surface_vertex_attributes = true
screen_space_labels = true
interactive_updates = true
```

but only after implementation.

## Presentation resolution

Suggested function:

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


def resolve_presentation_for_backend(
    presentation: ResolvedPresentation,
    capabilities: RendererCapabilities,
) -> BackendResolvedPresentation:
    ...
```

The function should be deterministic and pure.

## Fallback examples

### Dense vector field

Requested:

```text
high-density instanced arrows with per-instance color
```

Renderer lacks per-instance color but supports batched curves.

Resolved:

```text
batched vector geometry + bounded categorical/material fallback
```

Scientific vectors remain unchanged.

### Volumetric field

Requested cinematic volume, renderer lacks volumetrics.

Possible deterministic fallback:

```text
explicit scalar slices or isosurfaces
```

Only if the semantic visualization already provides a valid alternate view or the presentation plan explicitly allows that fallback.

A renderer must not invent an isosurface threshold.

### Screen-space labels

Requested screen-space legend, backend lacks it.

Fallback:

```text
world-space TextLabel presentation group
```

if readable.

### Depth of field

Requested cinematic DOF, unsupported.

Fallback:

```text
no DOF
```

This affects aesthetics only.

## Hard vs soft requirements

Not every presentation feature should silently degrade.

```python
class PresentationRequirementLevel(str, Enum):
    PREFERRED = "preferred"
    REQUIRED = "required"
```

A user may request:

```text
preferred volumetrics
required quantitative per-instance color
```

If a required feature cannot be represented faithfully, resolution should fail with a structured diagnostic rather than silently changing meaning.

## Quantitative color integrity

This is especially important.

If a scientific view requires a continuous quantitative color map and a backend cannot represent the values faithfully, do not degrade into a few arbitrary material bins without explicit policy.

Options:

- choose another valid renderer representation;
- decimate spatially while preserving value mapping;
- fail required-quality presentation;
- mark approximation clearly if the user explicitly allows it.

## Quality profile

A backend may additionally expose implementation-specific recommended limits through generic fields:

```text
max_recommended_glyphs
max_recommended_labels
```

These are hints, not hard scientific limits.

Presentation decimation should remain explicit and deterministic.

## Capability versioning

`RendererCapabilities` itself is a public contract.

Add new fields with conservative defaults where possible.

Do not reinterpret an existing field silently.

Backend version and capability profile may be recorded in presentation/export metadata for reproducibility of visual output.

## Incremental update capability

Distinguish:

```text
interactive_updates
incremental_geometry_updates
topology_preserving_updates
```

A backend might support interactive full rebuilds without stable native object identity. Another may support in-place updates.

Presentation/composer code should not assume all interactive backends are incremental.

## Renderer ownership

Capabilities do not change ownership rules.

Backend-created native resources remain backend-owned and must map from deterministic Spectra IDs where possible.

Switching renderer capability profiles must not rename scientific primitive IDs.

## Plugin renderer backends

Future renderer plugins may provide a backend factory plus capability profile.

Conceptual plugin metadata:

```python
@dataclass(frozen=True)
class RendererBackendDescriptor:
    backend_id: str
    display_name: str
    factory: Callable[[], Backend]
    static_capabilities: RendererCapabilities | None = None
```

Dynamic device-specific capabilities may still be queried after backend creation.

## Headless export

A headless renderer/export worker can use the same capability contract.

Example:

```text
remote worker supports post-processing and volumetrics
local WebGPU preview does not
```

The same presentation intent may resolve differently but deterministically, with recorded fallbacks.

## Tests after implementation gate

- conservative base profile;
- MemoryBackend capability inspection;
- Blender profile matches only validated features;
- deterministic fallback list;
- required unsupported feature fails;
- preferred unsupported feature degrades predictably;
- scientific Scene data unchanged by capability resolution;
- quantitative color requirement never silently becomes decorative color;
- capability profile serialization/introspection if later exposed through project/export metadata.

## Success criterion

A scientific domain should never contain code equivalent to:

```python
if backend == "blender":
    ...
elif backend == "webgpu":
    ...
```

The domain compiles science into a generic view. Presentation negotiation and renderer backends decide how to express that view faithfully on the available rendering technology.