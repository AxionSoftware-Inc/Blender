# Spectra Science — Presentation/Core Feasibility Audit

Status: **source review against current runtime; no runtime code changed**.

This audit checks whether the planned first premium-presentation implementation can be built on current Core contracts without prematurely changing Scene schema or renderer backends.

## Reviewed runtime contracts

Current source confirms the following generic primitives/resources already exist:

```text
Camera
Light
TextLabel
Material
Scene.active_camera_id
Scene.timeline
Bounds3D / scene_bounds
Transform3D.look_at
```

This is sufficient for a meaningful Phase 1 presentation composer.

## Camera support — sufficient for Phase 1

Current `Camera` supports:

```text
projection = perspective | orthographic
fov_y_radians
orthographic_scale
near_clip
far_clip
Transform3D
```

Current `Transform3D.look_at(eye, target, up=...)` creates a renderer-neutral camera-style transform with local `-Z` looking at the target.

Current bounds infrastructure provides:

```text
primitive_local_bounds(...)
scene_local_bounds(...)
primitive_bounds(...)
scene_bounds(...)
Bounds3D.center
Bounds3D.size
Bounds3D.diagonal
Bounds3D.bounding_sphere_radius
```

Therefore `fit_all`, simple perspective context framing, and orthographic analysis framing can be implemented without changing Core primitives.

### Recommended generic camera-fit helper

A presentation-private helper can compute:

```text
bounds = scene_bounds(scene)
center = bounds.center
radius = max(bounds.bounding_sphere_radius, epsilon)
```

Perspective distance can be derived from FOV and padded radius.

Orthographic scale can derive from max projected extent plus padding.

The first implementation should use a deterministic default viewing direction, with explicit overrides later.

Do not add Blender focal-length logic to generic camera fitting.

## Text labels — sufficient for basic presentation annotations

Current `TextLabel` has:

```text
text
position
size
color
transform
```

This is enough for:

- title;
- subtitle;
- time indicator;
- simple world-space quantity labels.

Limitation:

```text
no generic screen-space anchoring/layout contract yet
```

Therefore Phase 1 labels should be simple renderer-neutral/world-space labels or use a deterministic scene-relative placement convention.

Do not invent screen-pixel positioning in Core for the first presentation patch.

## Lighting — sufficient for generic intent

Current `Light` supports:

```text
ambient
directional
point
spot
color
intensity
range
spot angle
transform
```

This is sufficient for a generic `scientific_studio` light arrangement using deterministic key/fill/rim resources.

Important limitation:

`Light.intensity` is intentionally backend-neutral and not a physical photometric unit.

Therefore presentation presets may define relative visual lighting intent, but should not describe it as physically calibrated illumination.

## Materials — sufficient for basic style, not quantitative field attributes

Current `Material` supports:

```text
base_color
unlit | lit
metallic
roughness
emission_color
emission_strength
double_sided
```

This is sufficient for:

- generic analysis/cinematic material styling;
- luminous accents;
- unlit quantitative flat color where one color per primitive is enough;
- shared presentation-owned materials.

It is not yet a full quantitative scientific material system.

## PointCloud and VectorGlyphSet color support

Current batched primitives already support per-instance colors:

```text
PointCloud.colors
VectorGlyphSet.colors
```

This means quantitative/categorical per-instance color experiments can potentially be implemented for these primitives without changing the primitive schema.

Backend support still needs capability/validation checks.

The current Blender mapping must not be assumed to realize arbitrary high-cardinality per-instance color faithfully until that path is implemented and validated.

## Surface color limitation

Current `Surface` has only one primitive-level:

```text
color: Color
```

It does not currently carry:

```text
per-vertex colors
scalar attribute arrays
named generic vertex attributes
UV/scalar presentation channels
```

This is the most important presentation limitation discovered by the audit.

### Consequence

A real temperature/potential/stress colormap over one continuous `Surface` cannot be represented faithfully by current generic `Surface` semantics merely by presentation policy.

Do not hide this by:

- creating thousands of tiny separate Surface objects;
- letting Blender independently recover scientific scalar values;
- using a decorative material gradient unrelated to data.

### Recommended next step

Keep quantitative Surface color out of Phase 1.

When W3 quantitative-color work begins, evaluate a small generic attribute contract, for example conceptually:

```text
Surface vertex scalar values + named channel
or
Surface per-vertex colors
or
reusable generic AttributeBuffer resource
```

Choose only after examining multiple domains:

```text
temperature
potential
stress
probability density
CFD scalar slices
```

A generic attribute abstraction is preferable if several primitive types need the same mechanism.

Any Scene schema change should be deliberate/versioned, not smuggled into presentation code.

## Scene immutability — well suited to presentation composition

Current `Scene` is frozen/immutable and validates:

- unique primitive IDs;
- material references;
- group references/cycles;
- active camera;
- timeline target/property compatibility.

This is a good fit for:

```text
base Scene
  -> dataclass replacement/composition
  -> enriched Scene
```

The existing `spectra.presentation.staggered_reveal()` already follows this pattern through `dataclasses.replace`.

Phase 1 should preserve it.

## Timeline composition — current foundation is sufficient

Existing presentation helpers provide:

```text
merge_timelines(...)
staggered_reveal(...)
```

Current Scene validation checks that animation tracks reference real primitive IDs and valid property paths.

Therefore presentation reveal tracks can be composed with scientific tracks safely without making renderer time authoritative.

## Active camera — directly supported

`Scene.active_camera_id` already references a `Camera` primitive and is validated.

Therefore the presentation composer can:

1. preserve an existing active camera when policy says so;
2. replace/add a deterministic presentation-owned camera;
3. set `active_camera_id` to that camera;
4. keep scientific geometry unchanged.

No Scene schema change is necessary.

## Background/theme limitation

Current generic Scene does not have a first-class:

```text
background color
world/environment resource
post-processing profile
```

Therefore `theme="dark_lab"` cannot yet be fully expressed as generic Scene data without additional design.

### Phase 1 recommendation

Treat theme as presentation policy metadata that affects currently expressible resources such as:

- label colors;
- scientific/presentation material defaults;
- generic lights;

but defer actual renderer background/world interpretation to later backend capability work.

Do not add a `Scene.background` field casually just to make dark mode work.

If background intent proves useful across Blender/WebGPU/headless export, introduce a generic environment/presentation resource in its own checkpoint.

## Axes limitation

No dedicated `Axes` primitive currently exists.

However basic axes can be composed from existing generic primitives:

```text
Polyline
TextLabel
Group
```

This is acceptable for an initial reusable axes composer.

Do not add a subject-specific axes implementation to scientific domains.

Advanced tick/grid/layout semantics should be a later presentation utility.

## Legend limitation

No dedicated Legend primitive exists.

A simple legend can initially be composed from:

```text
TextLabel
Region
Polyline
Group
```

But quantitative gradient legends may require richer color-ramp/attribute presentation semantics.

Therefore Phase 1 can support basic text/vector-scale legends, while W3 owns true quantitative colorbar behavior.

## Group semantics

Current `Group` is organizational by child IDs; generic transform inheritance is not a universal contract.

Presentation must not assume moving/scaling a Group automatically transforms children.

Camera framing and layout should operate on actual child primitive bounds rather than imagined group transforms.

## Phase 1 feasibility result

### Can implement without Core schema changes

```text
PresentationIntent value types
preset resolution
camera fit/orientation
active camera selection
basic lights
simple title/subtitle/time labels
staggered reveal/timeline composition
presentation deterministic IDs
basic material styling
basic axes from existing primitives
```

### Should defer

```text
true renderer background/world resource
quantitative continuous Surface colormaps
screen-space UI labels
advanced colorbars
volumetrics
post processing
Geometry Nodes/renderer instancing policy
```

## Suggested first camera implementation

Use a presentation-private helper rather than changing Core:

```python
def make_fit_camera(
    scene: Scene,
    *,
    camera_id: str,
    projection: str,
    padding: float,
    view_direction: Vec3,
    up: Vec3,
) -> Camera:
    ...
```

It can reuse:

```text
scene_bounds
Transform3D.look_at
Camera
```

If several non-presentation systems later need identical camera fitting, promote only then to a generic Core utility.

## Suggested first light rig

Presentation-private deterministic IDs:

```text
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Using current generic lights:

```text
directional/point/ambient
```

Exact relative intensities belong to preset defaults, not Blender nodes.

## Architectural conclusion

The current semantic/Scene engine already contains enough renderer-neutral geometry, camera, lighting, text, bounds, materials, immutability, and timeline infrastructure for a real Premium Presentation Phase 1.

The main missing generic capability for later quantitative premium science is not another renderer abstraction—it is a clean data-attribute path for continuous scalar/color fields on surfaces and potentially other dense primitives.

That should be treated as a separate, evidence-driven generic visualization contract rather than being prematurely embedded into Blender-specific materials.