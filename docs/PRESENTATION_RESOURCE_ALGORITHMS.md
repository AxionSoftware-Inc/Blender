# Spectra Science — Deterministic Presentation Resource Algorithms

Status: **design/source-facing contract, not implemented runtime**.

This document turns the presentation resource namespace into deterministic algorithms suitable for direct implementation after the current runtime validation gate.

## Goal

Given the same:

```text
base Scene
PresentationIntent
PresentationContext
presentation variant identity
```

the presentation composer should produce the same presentation-owned resource IDs, ordering, and roles every time.

The algorithm must not depend on:

- Python object memory addresses;
- random UUIDs;
- Blender datablock names;
- process-local hashes;
- dictionary insertion accidents;
- current wall-clock time.

## Canonical resource key

Use an immutable semantic key conceptually equivalent to:

```python
@dataclass(frozen=True, order=True)
class PresentationResourceKey:
    category: str
    role: str
    instance: str = "primary"
    scope: str | None = None
```

Examples:

```text
(camera, primary, primary)
(light, key, primary)
(light, fill, primary)
(legend, temperature, primary)
(annotation, time, primary)
(axes, world, primary)
```

`scope` is used only when the same semantic role legitimately appears more than once, for example comparison panes.

## Canonical ID encoding

Recommended first algorithm:

```text
presentation.<category>.<role>[.<scope>][.<instance>]
```

Rules:

1. lowercase ASCII machine identifiers only;
2. segments use `[a-z0-9_]+`;
3. empty/default `instance=primary` may be omitted when unambiguous;
4. no user-facing localized labels in IDs;
5. no random suffixes;
6. semantic scientific IDs are never rewritten.

Examples:

```text
presentation.camera.primary
presentation.light.key
presentation.light.fill
presentation.legend.temperature
presentation.legend.temperature.left
presentation.annotation.time
presentation.axes.slice_xy
```

## Collision handling

Collisions must fail deterministically rather than invent random suffixes.

If two resources resolve to the same key but represent different intended resources, the composer should raise a structured presentation diagnostic indicating the conflicting semantic roles.

Allowed case:

```text
same key + same resolved resource semantics -> deduplicate/share
```

Disallowed case:

```text
same key + different quantity/range/target -> conflict
```

## Ordering

Presentation-owned resources should be appended/organized in deterministic category order.

Suggested initial ordering:

```text
1 camera
2 lights
3 context geometry
4 axes/grid
5 legends/scales
6 annotations
7 titles/subtitles
8 presentation groups
```

Within one category sort by canonical resource ID.

This gives stable Scene equality/serialization and predictable native-object mapping.

Scientific primitive ordering from the base Scene should remain unchanged.

## Camera algorithm

Camera composition works in **Scene-local coordinates**.

Use:

```text
scene_local_bounds(scene)
```

not world/parent-mapped bounds because the backend later applies `Scene.frame` to the root.

Basic deterministic camera fit:

```text
bounds -> center, radius/extents
preset -> projection + view direction + padding
view direction + up -> Transform3D.look_at(...)
```

Default analysis direction may be a fixed normalized vector chosen once in the preset contract.

Do not derive direction from renderer viewport state.

If the base Scene already has an active camera, policy must explicitly choose:

```text
preserve
replace_with_presentation_camera
fit_existing_camera (later)
```

No implicit renderer-state inspection.

## Light-rig algorithm

For `scientific_studio`, generate a fixed semantic rig from Scene-local bounds.

Conceptual roles:

```text
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Positions/directions derive from bounds center/radius and fixed normalized rig directions.

Intensity values are presentation-relative because generic `Light.intensity` is backend-neutral.

For unlit/analysis data, the rig may be reduced or omitted deterministically.

## Title and annotation placement

Until screen-space layout exists, Phase 1 labels use deterministic Scene-local world placement.

Example:

```text
bounds maximum + padded offset
```

The placement must derive only from Scene geometry and resolved presentation policy.

Avoid pixel assumptions.

Renderer-specific billboard/screen-space behavior can be a later capability-resolved mapping.

## Axes algorithm

First axes implementation may use existing:

```text
Polyline + TextLabel + Group
```

Axis extent derives from Scene-local bounds or explicit view metadata.

Axes cannot assume all scenes mean Cartesian x/y/z. `PresentationContext` or view metadata may provide axis labels/units.

If axis semantics are unknown, prefer no labels rather than guessing.

## Legend identity

Legend key should derive from semantic quantity/range role, not palette display name alone.

Conceptual source:

```text
quantity identifier
display component
comparison scope
```

Examples:

```text
temperature
pressure_delta
probability_density
phase
velocity_magnitude
```

Two visualizations sharing exactly the same resolved scale may share one legend if the layout policy allows it.

Two different ranges must not silently share one legend.

## Color-policy fingerprint

For later quantitative color resources, derive a canonical presentation-only fingerprint from resolved display semantics, for example:

```text
quantity id
scale kind
palette id
range mode
resolved min/max/center
clamp behavior
unit display
```

This fingerprint may be used for cache/material sharing, but the user-facing Scene resource ID should remain semantic and readable.

Do not use Python's built-in `hash()` for persistent identity.

## Resource diff

Preset switching should compare previous and next presentation resource maps by canonical key.

Pseudo-algorithm:

```text
old keys ∩ new keys -> update if value changed
old keys - new keys -> remove presentation-owned resource
new keys - old keys -> create
scientific IDs -> untouched
```

The diff is presentation-semantic. Native backends may realize updates differently.

## Timeline ownership

Presentation animation may only add a track if `(target_id, property_path)` is not already owned by the scientific/base timeline unless an explicit composition operator exists.

Current `Timeline` rejects duplicate target/property paths, so Phase 1 should use the conflict rules from `ANIMATION_COMPOSITION_CONTRACT.md`.

Preferred behavior:

```text
scientific track exists -> skip/reject conflicting reveal
presentation-owned new primitive -> presentation may animate freely
```

## Idempotence

A key acceptance property:

```python
compose_presentation(compose_presentation(base, intent), intent)
```

should not accumulate duplicate presentation resources.

The first implementation may achieve idempotence by removing/replacing resources in the reserved `presentation.*` namespace before recomposition, while always preserving scientific resources.

Later implementations may use semantic diff/update.

## Variant handling

If only one presentation variant is instantiated into a Scene at once, use simple IDs:

```text
presentation.camera.primary
```

If several variants coexist in one Scene graph, introduce an explicit variant scope:

```text
presentation.variant.<variant_id>.camera.primary
```

Do not add variant prefixes preemptively to scientific IDs.

## Validation rules

Before returning the enriched Scene:

- all IDs unique;
- every presentation ID conforms to namespace rules;
- active camera references a real `Camera`;
- every group child exists;
- every material reference exists;
- no duplicate timeline target/property pair;
- presentation resources do not shadow scientific IDs;
- generated numeric values finite;
- camera clipping valid;
- light intensity/range valid.

Normal `Scene` validation should remain the final structural authority.

## Implementation helpers

Recommended private functions for Phase 1:

```python
def presentation_resource_id(key: PresentationResourceKey) -> str: ...
def strip_presentation_resources(scene: Scene) -> Scene: ...
def make_fit_camera(scene: Scene, policy: CameraPolicy) -> Camera: ...
def make_light_rig(scene: Scene, policy: LightingPolicy) -> tuple[Light, ...]: ...
def make_basic_annotations(scene: Scene, policy: AnnotationPolicy) -> tuple[TextLabel, ...]: ...
def presentation_track_conflicts(scene: Scene, tracks: tuple[Track[object], ...]) -> tuple[...]: ...
```

These should remain renderer-neutral and pure where possible.

## Tests after implementation gate

- same input produces identical IDs/order;
- scientific IDs preserved;
- repeated composition produces no duplicates;
- non-default `Scene.frame` camera fit remains correct in Scene-local space;
- resource collision fails deterministically;
- preset switch removes obsolete presentation resources only;
- base scientific timeline conflict is detected;
- presentation-owned timeline tracks remain valid;
- no random/process-dependent IDs;
- serialization equality for repeated deterministic composition once presentation resources are persisted as ordinary Scene primitives.

## Success criterion

Presentation composition should behave like a deterministic compiler pass over a scientific Scene, not like an imperative renderer script that creates whatever native objects happen to be convenient on each run.
