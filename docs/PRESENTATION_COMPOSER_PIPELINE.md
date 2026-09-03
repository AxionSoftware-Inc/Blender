# Spectra Science — Presentation Composer Pass Pipeline

Status: **design pipeline, not implemented runtime**.

This document defines the deterministic pass order for converting a scientifically correct base `Scene` into a presentation-enriched `Scene`.

The order matters because camera bounds, presentation-owned resources, timeline ownership, and idempotence interact.

## Input contract

Inputs:

```text
base_scene: Scene
intent: PresentationIntent
context: PresentationContext | None
```

Assumptions:

- `base_scene` was created by semantic visualization, not by a renderer;
- scientific primitive IDs are stable;
- scientific timeline is authoritative;
- presentation composer does not solve/recompute scientific domains.

## Pass 0 — validate and resolve policy

```text
PresentationIntent
    -> resolve preset defaults
    -> apply explicit overrides
    -> validate resolved policy
```

Output:

```text
ResolvedPresentation
```

No Scene mutation/composition yet.

Validation includes:

- finite numeric policy values;
- valid padding/ranges;
- valid color semantics;
- compatible annotation/camera modes;
- no renderer-native options.

## Pass 1 — strip/reconcile previous presentation-owned resources

For idempotent recomposition, identify reserved resources:

```text
presentation.*
```

Scientific primitives remain untouched.

First implementation may simply remove existing presentation-owned primitives/materials/tracks before regenerating them.

Later implementation may compute semantic diffs for in-place updates.

Do not remove a user/scientific resource merely because it has similar display purpose; ownership is determined by reserved Spectra presentation identity.

## Pass 2 — capture scientific content set

Freeze the IDs/geometry that count as scientific base content for this composition.

This set is used for:

- camera fitting;
- scientific-vs-presentation validation;
- reveal selection;
- preservation checks.

Presentation resources created in later passes must not feed back into scientific bounds unless explicitly requested by layout semantics.

## Pass 3 — compute Scene-local framing data

Use:

```text
scene_local_bounds(scientific_scene)
```

or primary-object bounds when policy/context requests `FIT_PRIMARY`.

Do this **before** adding title, legends, axes, and presentation lights.

Output conceptual data:

```text
PresentationLayoutContext
  scientific_bounds
  center
  extent/radius
  primary bounds optional
  semantic axes/frame hints optional
```

## Pass 4 — create/update presentation camera

Using resolved camera policy and layout context:

```text
presentation.camera.primary
```

unless preserving an existing active camera.

Camera transform stays Scene-local.

Set final `active_camera_id` only after validating the new Camera resource.

Do not ask Blender/WebGPU for viewport orientation.

## Pass 5 — create generic light rig

Generate renderer-neutral `Light` primitives where policy requires them.

Example deterministic roles:

```text
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Lighting derives from scientific bounds and preset semantics.

No Blender nodes/compositor settings here.

## Pass 6 — create axes/context geometry

If requested and semantically meaningful:

```text
Polyline
TextLabel
Group
```

with deterministic IDs.

Axes labels/units come from context/view metadata.

If semantics are unknown, do not guess x/y/z labels.

Context/reference geometry may also be introduced here if the explicit view/presentation contract requests it.

## Pass 7 — resolve quantitative presentation bindings

This pass exists conceptually even before full visual attributes are implemented.

For each explicit quantitative visual channel:

```text
quantity metadata
+ source values/range metadata
+ ColorScalePolicy
-> ResolvedColorScale
```

Do not alter scientific values.

If current generic Scene cannot express the required quantitative mapping faithfully (for example continuous scalar Surface color before visual attributes), return a structured unsupported/deferred diagnostic rather than fake it.

## Pass 8 — create legends/scales

Legends derive from the **already resolved** quantitative scale.

They do not compute their own min/max independently.

Initial representation may use ordinary generic primitives.

Deterministic IDs:

```text
presentation.legend.<quantity_role>
```

A legend is added only when it explains actual visual encoding.

## Pass 9 — create annotations/title/time resources

Add deterministic presentation-owned labels:

```text
presentation.title.primary
presentation.annotation.time
presentation.annotation.<semantic_role>
```

Phase 1 uses Scene-local/world-space text placement.

Time annotation semantics should derive from engine time and be updateable without numerical recomputation.

## Pass 10 — assign presentation materials/styles

Add/reuse presentation-owned generic `Material` resources for context, annotation, axes, etc.

Scientific primitive colors/materials should not be overwritten casually.

Quantitative data material behavior must preserve resolved color semantics.

Do not introduce one material per dense scalar sample.

## Pass 11 — plan presentation animation

Generate presentation tracks only after all target presentation primitives exist.

Possible Phase 1 animation:

```text
staggered reveal
simple label fade
```

Before merge, check ownership conflicts against the scientific timeline.

Current `Timeline` requires unique `(target_id, property_path)` pairs.

Rules:

- presentation-owned primitive properties are safe if unique;
- scientific property track exists -> presentation does not add competing track;
- no last-writer-wins merge.

## Pass 12 — merge timeline

Use a validated merge of:

```text
scientific timeline
presentation timeline
```

Duration becomes the deterministic max/combined duration according to existing engine semantics.

The output timeline remains engine-owned.

## Pass 13 — assemble immutable Scene

Construct the final Scene with:

```text
original scientific primitives preserved
+ deterministic presentation primitives
original scientific materials preserved
+ presentation materials
resolved active camera
merged timeline
same Scene.frame
```

Avoid mutating the input Scene.

## Pass 14 — final structural validation

Normal `Scene` constructor validation should catch:

- duplicate primitive IDs;
- invalid material references;
- group cycles/missing children;
- invalid active camera;
- timeline target/property mismatches.

Presentation-specific validation additionally checks:

- all added resources use reserved IDs;
- scientific IDs/value arrays unchanged;
- deterministic resource map;
- required quantitative semantics satisfied;
- no presentation/scientific timeline ownership conflicts.

## Pass 15 — optional backend capability resolution

This is **not Phase 1**.

Later:

```text
presentation-enriched generic Scene/plan
+ BackendCapabilities
-> backend-resolved presentation fallbacks
```

Required scientific visual semantics must not silently degrade.

Backend resolution must not recalculate physics or change scientific values.

## Why backend negotiation is later

Initial composer should first prove:

```text
pure deterministic generic presentation composition
```

Then Blender/WebGPU capability-specific realization can be tested independently.

This keeps failures easy to isolate.

## Pure-function structure

Recommended implementation style:

```python
def resolve_presentation(intent) -> ResolvedPresentation: ...
def compute_layout_context(scene, resolved, context) -> PresentationLayoutContext: ...
def compose_resources(scene, resolved, layout, context) -> PresentationResources: ...
def compose_presentation(scene, intent, *, context=None) -> Scene: ...
```

Keep native renderer side effects outside these functions.

## Deterministic intermediate plan

A useful internal immutable DTO may be:

```python
@dataclass(frozen=True)
class PresentationPlan:
    resolved: ResolvedPresentation
    camera: Camera | None
    lights: tuple[Light, ...]
    primitives: tuple[Primitive, ...]
    materials: tuple[Material, ...]
    tracks: tuple[Track[object], ...]
    active_camera_id: str | None
    diagnostics: tuple[PresentationDiagnostic, ...] = ()
```

Then:

```text
plan generation
-> validate plan
-> apply plan to base Scene
```

This makes testing easier than one giant function.

## Idempotence model

First implementation can guarantee:

```text
strip old presentation resources
-> regenerate deterministic plan
```

so:

```python
compose_presentation(compose_presentation(base, intent), intent)
```

produces an equivalent result rather than duplicate cameras/lights/titles.

Later diff/update logic can optimize without changing semantics.

## Failure behavior

Presentation failure must not corrupt/replace the scientific Scene.

Because composition is immutable/pure, errors simply fail to return the new Scene.

Categories may include:

```text
invalid_presentation_policy
missing_primary_primitive
camera_fit_failed
animation_property_conflict
quantitative_mapping_unsupported
presentation_resource_collision
backend_requirement_unavailable (later)
```

## Phase 1 implementation subset

Implement only:

```text
Pass 0 policy resolution
Pass 1 strip deterministic presentation resources
Pass 2 scientific content capture
Pass 3 local bounds
Pass 4 camera
Pass 5 basic lights
Pass 9 title/time labels
Pass 11/12 simple reveal with conflict detection
Pass 13/14 immutable assembly/validation
```

Axes may be included if small and clean.

Quantitative color/legend stays a separate checkpoint if it requires new visual attributes.

## Tests after implementation gate

- pass ordering deterministic;
- camera unaffected by title/legend placement;
- presentation resources do not alter base bounds used for fitting;
- input Scene unchanged;
- `Scene.frame` preserved exactly;
- scientific primitive ordering/IDs preserved;
- idempotent recomposition;
- conflict leaves base Scene usable;
- presentation-only changes do not invoke domain solver/capability code;
- MemoryBackend/BackendSession can consume resulting Scene.

## Success criterion

Premium presentation should behave as a sequence of explicit deterministic compiler passes over a renderer-neutral scientific Scene. Each pass has one responsibility, can be independently tested, and cannot quietly leak renderer state back into science.
