# Spectra Science — Presentation/Core Feasibility Audit

Status: **source review against current runtime; no runtime code changed**.

This audit checks whether Premium Presentation Phase 1 can be built on current Core contracts without prematurely changing Scene schema or renderer backends.

## Current generic foundation

Source confirms these renderer-neutral contracts already exist:

```text
Camera
Light
TextLabel
Material
Scene.active_camera_id
Scene.timeline
Bounds3D
scene_local_bounds(...)
scene_bounds(...)
Transform3D.look_at(...)
```

This is sufficient for a meaningful Phase 1 composer.

## Critical coordinate-frame invariant

`Scene.frame` maps Scene-local scientific coordinates into the parent/renderer world.

Blender currently applies that frame as the Spectra root object's world matrix. Primitive transforms—including `Camera.transform`—are then applied **under that root**, so they are Scene-local.

Therefore a presentation-owned camera that frames Scene primitives must normally use:

```python
scene_local_bounds(scene)
```

not:

```python
scene_bounds(scene)
```

when constructing the Camera primitive's local transform.

Using parent/world-mapped bounds to construct a local camera could apply a non-default coordinate frame twice after the backend applies `Scene.frame` again.

Use `scene_bounds()` only when a consumer explicitly needs parent/world-mapped bounds outside the Scene-local primitive coordinate system.

This invariant should receive a regression test with a non-identity `CoordinateFrame3D` when presentation runtime is implemented.

## Camera support — sufficient

Current `Camera` supports:

```text
perspective | orthographic
fov_y_radians
orthographic_scale
near/far clip
Transform3D
```

`Transform3D.look_at(eye, target, up)` creates a camera-style transform whose local `-Z` looks at the target.

`Bounds3D` provides:

```text
center
size
diagonal
bounding_sphere_radius
```

Therefore the first presentation implementation can build deterministic:

```text
fit_all
perspective_context
orthographic_analysis
```

without Core changes.

### Recommended helper

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
    bounds = scene_local_bounds(scene)
    ...
```

Perspective distance can derive from padded bounding radius and vertical FOV. Orthographic scale can derive from the relevant local extent plus padding.

Do not add Blender focal-length concepts to generic presentation code.

## Text labels — sufficient for basic annotations

Current `TextLabel` provides:

```text
text
position
size
color
transform
```

Enough for:

- title;
- subtitle;
- time indicator;
- simple world-space labels.

Current limitation:

```text
no generic screen-space anchoring/layout
```

Phase 1 should therefore use deterministic Scene-local/world-space placement. Do not invent screen-pixel coordinates in Core.

## Lighting — sufficient for first presentation rigs

Current generic `Light` supports:

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

This is enough for deterministic presentation-owned key/fill/rim or flat-analysis rigs.

`Light.intensity` is intentionally renderer-neutral, not a calibrated photometric unit.

## Materials — useful but not a quantitative attribute system

Current `Material` supports:

```text
base_color
lit | unlit
metallic
roughness
emission
alpha
double-sided
```

This is enough for basic presentation style and reusable visual materials.

It does not solve dense quantitative scalar coloring by itself.

## Existing dense color support

Current:

```text
PointCloud.colors
VectorGlyphSet.colors
```

already allow per-instance resolved colors in generic Scene semantics.

Backend capability remains separate: current Blender realizes these through a bounded material-slot path rather than a scalable float-attribute shader path.

## Surface limitation

Current `Surface` has:

```text
vertices
triangles
one uniform color
```

It does not carry:

```text
per-vertex colors
scalar attributes
named vertex attributes
```

Therefore a physically meaningful continuous temperature/potential/stress/probability colormap over one Surface cannot currently be represented generically.

Do not work around this by creating thousands of tiny Surface objects or letting Blender reconstruct scalar science independently.

See `VISUAL_ATTRIBUTE_MODEL.md` for the later dedicated work package.

## Scene immutability — ideal for composition

Current `Scene` is frozen and validates:

- unique primitive/material IDs;
- material references;
- groups/cycles;
- active camera;
- timeline target/property paths.

Existing `staggered_reveal()` already uses `dataclasses.replace` to create a new Scene rather than mutating input state.

Phase 1 should preserve that pattern.

## Timeline support — sufficient

Existing:

```text
merge_timelines(...)
staggered_reveal(...)
```

can compose presentation tracks with scientific tracks.

Presentation must not rescale or replace scientific time silently.

## Active camera — directly supported

`Scene.active_camera_id` already validates that the referenced primitive is a Camera.

The composer can therefore add/replace a deterministic presentation camera and activate it without Scene schema changes.

## Theme/background limitation

Current generic Scene has no first-class:

```text
world/background resource
post-processing profile
```

Therefore Phase 1 `dark_lab`/theme intent can influence currently expressible presentation resources such as labels/materials/lights, but a real renderer world/background contract is deferred.

Do not add `Scene.background` casually just to implement dark mode.

## Axes and legends

No dedicated Axes or Legend primitive exists.

Basic versions can be composed from:

```text
Polyline
TextLabel
Region
Group
```

This is adequate for early analysis/presentation utilities.

Advanced tick layout and quantitative gradient colorbars belong to later presentation/color packages.

## Group semantics

`Group` currently owns organizational child references, not universal transform inheritance.

Presentation layout/camera framing must inspect actual child primitive geometry rather than assume group transforms affect children.

## Phase 1 feasibility result

### Can implement without Core schema changes

```text
PresentationIntent/policies
preset resolution
Scene-local camera fit/orientation
active camera
basic lights
simple title/subtitle/time labels
staggered reveal/timeline merge
deterministic presentation IDs
basic material styling
basic axes made from existing primitives
```

### Defer

```text
renderer world/background resource
continuous Surface scalar colormaps
screen-space labels
advanced colorbars
volumetrics
post processing
Geometry Nodes/renderer instancing policy
```

## First light rig

Presentation-owned deterministic IDs:

```text
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Exact relative intensities belong to preset defaults, not Blender node names.

## Required frame regression when implemented

Create the same local scientific Scene under:

```text
WORLD_FRAME
and
a translated/rotated non-identity CoordinateFrame3D
```

Compose a fit camera in each case.

Assert the Camera primitive remains correctly Scene-local and the backend/frame transform moves camera and science together without double-transforming the camera target.

## Architectural conclusion

Current Core already has enough generic geometry, camera, lighting, text, bounds, materials, immutability, coordinate frames, and timeline semantics for Premium Presentation Phase 1.

The main later generic gap is a dense scalar/color attribute path—not another renderer-specific scientific subsystem.