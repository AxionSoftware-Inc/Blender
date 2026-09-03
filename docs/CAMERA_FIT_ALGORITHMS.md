# Spectra Science — Renderer-Neutral Camera Fit Algorithms

Status: **design algorithm, not implemented runtime**.

This document defines deterministic Scene-local camera fitting formulas for the first premium presentation implementation.

It is grounded in current generic contracts:

```text
scene_local_bounds(...)
Bounds3D
Camera
Transform3D.look_at(...)
```

## Coordinate rule

All automatic presentation camera calculations operate in **Scene-local coordinates**.

The backend later maps the entire Scene through `Scene.frame`.

Therefore:

```text
camera fit input = scene_local_bounds(scene)
```

not parent/world-mapped bounds.

## Inputs

Conceptual helper:

```python
def fit_camera(
    scene: Scene,
    *,
    projection: Literal["perspective", "orthographic"],
    view_direction: Vec3,
    up: Vec3,
    padding: float,
    fov_y_radians: float,
    aspect_ratio: float | None = None,
) -> Camera:
    ...
```

The first generic Scene contract does not own viewport pixel dimensions, so `aspect_ratio` may initially be omitted or supplied by presentation/export context.

If unknown, use a deterministic neutral assumption such as 16:9 only in a product/output-specific layer, or fit conservatively from bounding sphere in the generic composer.

## Bounds

Start with:

```text
bounds = scene_local_bounds(scene)
center = bounds.center
radius = max(bounds.bounding_sphere_radius, epsilon)
```

Suggested epsilon:

```text
max(bounds.diagonal * 1e-6, 1e-6)
```

This prevents degenerate point/line scenes from creating zero-distance cameras.

## Padding

Interpret presentation `padding` as a fractional margin around the fitted extent.

For example:

```text
padding = 0.10
padded_radius = radius * 1.10
```

Require finite `padding >= 0`.

Do not reuse `Bounds3D.padded()` directly if its parameter means multiplicative factor >= 1; translate presentation padding explicitly to avoid semantic confusion.

## View direction

`view_direction` means direction from camera toward target.

Require:

- finite components;
- non-zero magnitude;
- normalized before use.

The eye is placed opposite the viewing direction:

```text
eye = center - direction * distance
```

Then:

```text
Transform3D.look_at(eye, center, up=up)
```

Current camera convention uses local `-Z` forward.

## Up-vector fallback

`Transform3D.look_at()` rejects an up vector parallel to the viewing direction.

Presentation helper should choose a deterministic fallback rather than random perturbation.

Conceptual:

```text
preferred up = (0, 0, 1) or preset-defined
if |direction dot up| > threshold:
    fallback to another canonical axis least aligned with direction
```

A deterministic rule can choose the world-local basis axis with minimum absolute dot product against the view direction.

## Perspective fit using bounding sphere

For a conservative aspect-independent fit:

```text
half_fov = fov_y / 2
required_distance = padded_radius / sin(half_fov)
```

This places the entire bounding sphere inside the vertical field of view.

An alternative tangent-based formula fits a planar half-height, but sphere/sine fit is conservative for 3D extent.

Require:

```text
0 < fov_y < pi
```

matching current `Camera` validation.

## Perspective near/far clip

Given:

```text
d = camera-target distance
r = padded_radius
```

choose conservative clipping such as:

```text
near = max(epsilon_clip, d - 1.5*r)
far  = max(near + epsilon_clip, d + 1.5*r)
```

The exact multiplier is presentation policy and can be tuned after tests.

Rules:

- near > 0;
- far > near;
- no content clipping for canonical bounds;
- avoid absurdly tiny near plane if not needed because depth precision suffers in realtime renderers.

## Orthographic fit

Current `Camera.orthographic_scale` is a generic positive scalar interpreted by backends as native orthographic scale.

For aspect-independent conservative fitting:

```text
orthographic_scale = 2 * padded_radius
```

This fits the bounding sphere.

For known output aspect ratio, a tighter implementation may project all 8 bounds corners into camera right/up axes and choose scale from vertical extent plus horizontal/aspect requirement.

That is preferable for publication layouts once output aspect is explicit.

## Aspect-aware projection algorithm

Given normalized camera basis:

```text
right
up_corrected
forward
```

For each `Bounds3D.corner` compute offsets from center and project:

```text
x = dot(offset, right)
y = dot(offset, up_corrected)
z = dot(offset, forward)
```

Then:

```text
half_width = max(abs(x))
half_height = max(abs(y))
```

Orthographic scale, if defined as full vertical height:

```text
required_half_height = max(
    half_height,
    half_width / aspect_ratio,
)
orthographic_scale = 2 * required_half_height * (1 + padding)
```

For perspective, aspect-aware exact fitting is more involved because depth varies across corners. A robust first implementation may use bounding sphere until tests justify tighter frustum fitting.

## FIT_ALL vs FIT_PRIMARY

`FIT_ALL`:

```text
bounds from all visible scientific geometry
```

Presentation camera/light/text resources should normally be stripped/ignored before fitting so composition is not self-referential.

`FIT_PRIMARY`:

```text
bounds from the primitive/group explicitly identified by PresentationContext.primary_primitive_id
```

If the primary ID is invalid or has no geometry, return a structured presentation diagnostic rather than silently choosing a random object.

## Which primitives affect framing

Current bounds helpers intentionally exclude:

```text
Camera
Light
Group as geometry
```

TextLabel produces an anchor-point bound.

For presentation auto-fit, it may be desirable to frame scientific geometry **before** adding title/legend annotations so labels do not push the camera away from the science.

Recommended phase order:

```text
base scientific Scene
-> compute scientific bounds
-> create camera/light rig
-> add annotations/axes/legends
```

## Existing camera preservation

Policy must be explicit.

Suggested camera modes:

```text
preserve_existing
fit_all
fit_primary
orthographic_analysis
perspective_context
```

If `preserve_existing` and `Scene.active_camera_id` is valid, do not replace it.

If auto-fit mode is selected, create/update deterministic `presentation.camera.primary`.

## Animated scientific geometry

A static fitted camera based only on `t=0` may clip later states.

Phase 1 choices must be explicit:

```text
fit_initial
fit_reference_scene
fit_sampled_envelope (later)
follow_subject (later)
```

For first canonical animated scenes, presentation context can provide known envelope/reference bounds or tests can assert start/mid/end remain inside frame.

Do not silently inspect thousands of timeline samples in a lightweight composer.

## Camera animation

Orbit/follow animation is later than basic fit.

When introduced:

- camera primitive has a deterministic presentation ID;
- camera tracks own `transform.translation` / `transform.rotation` only if no conflicting track exists;
- paths derive from generic presentation semantics;
- Blender keyframes are not scientific source of truth.

## Deterministic preset starting directions

Exact values should be fixed once accepted visually.

Conceptual examples only:

```text
analysis 3D: normalized (1, -1, 0.8)
context/cinematic: normalized (1.2, -1.5, 0.9)
2D slice analysis: normal to semantic slice plane
```

Do not derive default direction from Blender viewport orientation.

For semantic 2D views, view metadata should supply the preferred normal/up axes.

## Numerical validation after implementation

For each camera generated:

- transform values finite;
- camera-to-target distance positive;
- `Camera` constructor validation passes;
- all selected bounds corners lie inside the intended frustum within tolerance;
- non-default `Scene.frame` does not alter local fit result unexpectedly;
- repeated fit yields exactly equal Camera value objects for equal inputs.

## Canonical tests

1. unit cube centered at origin;
2. translated rectangular box;
3. very thin planar slice;
4. near-degenerate line;
5. single point cloud cluster;
6. scene with non-default `CoordinateFrame3D`;
7. existing active camera preserve mode;
8. primary-primitive fit among several distant objects.

## Success criterion

Automatic framing should be predictable mathematical composition over renderer-neutral Scene geometry. The same base Scene and presentation policy must produce equivalent generic camera semantics for Blender, WebGPU, and future backends without querying any renderer viewport state.
