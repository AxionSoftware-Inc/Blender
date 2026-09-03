# Spectra Science — Presentation Runtime Test Fixtures

Status: **design fixtures for the first presentation runtime checkpoint; no runtime implementation yet**.

This document defines small deterministic input Scenes and exact semantic expectations for Premium Presentation Phase 1. The goal is to make the first implementation test-driven without tying tests to Blender pixels or renderer-native names.

## Fixture principles

Fixtures must be:

- tiny enough to inspect by eye;
- renderer-neutral;
- deterministic;
- expressed using current Scene v4 primitives only;
- independent of numerical-domain availability;
- explicit about Scene-local coordinates;
- suitable for MemoryBackend tests before Blender tests.

No fixture should require GPU execution.

## Common IDs

Scientific fixture IDs:

```text
science.point.a
science.line.path
science.surface.patch
science.vector.field
science.label.source
science.camera.existing
```

Presentation-owned IDs must use:

```text
presentation.*
```

Tests should assert that scientific IDs are preserved exactly.

## F1 — Empty Scene

Input:

```python
Scene()
```

Expected behavior:

- policy resolution succeeds;
- no scientific geometry exists;
- composer must not create an invalid auto-fit camera from nonexistent bounds;
- presentation may return the Scene unchanged or add only resources explicitly requested by policy if a deterministic no-content convention exists;
- no NaN/inf transform or clip values;
- repeated composition is equal/idempotent.

This fixture defines empty-scene behavior explicitly rather than letting camera math fail accidentally.

## F2 — One Point at Origin

Input concept:

```text
Point(id="science.point.a", position=(0,0,0), radius=0.25)
```

Expected analysis presentation:

- `science.point.a` unchanged;
- one deterministic presentation camera if auto-camera enabled;
- camera ID exactly `presentation.camera.primary`;
- finite camera transform;
- camera targets Scene-local origin;
- near clip > 0;
- far clip > near clip;
- no scientific timeline added/changed;
- composing twice produces the same Scene value.

## F3 — Asymmetric Bounds

Input geometry spans approximately:

```text
x: -2 .. 6
y: -1 .. 3
z:  0 .. 2
```

Expected:

- computed center = `(2, 1, 1)` in Scene-local coordinates;
- auto-fit uses scientific content bounds before presentation annotations are added;
- title/axes/legend geometry does not expand the camera-fit target in the same composition pass;
- deterministic default view direction produces identical transform on repeated runs.

This fixture should be the main camera-fit regression.

## F4 — Non-default CoordinateFrame3D

Input:

- simple local geometry around origin;
- Scene frame translated/rotated away from world frame.

Expected:

- presentation camera is derived from `scene_local_bounds()`;
- camera transform is Scene-local;
- backend root/frame transform applies once;
- changing only Scene.frame while keeping local scientific geometry identical must not cause the composer to bake the frame into scientific vertices;
- no double transform.

This fixture protects the coordinate-frame invariant discovered during source audit.

## F5 — Existing Scientific Camera

Input:

- scientific geometry;
- `Camera(id="science.camera.existing", ...)`;
- `active_camera_id="science.camera.existing"`.

Two tests:

### preserve-existing mode

Expected:

- existing camera remains active;
- no duplicate presentation camera created.

### force-presentation-camera mode

Expected:

- scientific camera remains in Scene;
- new `presentation.camera.primary` is added;
- `active_camera_id` switches to presentation camera;
- scientific camera ID/content remain unchanged.

## F6 — Existing Scientific Timeline

Input:

- a Polyline or Surface with a scientific geometry track;
- timeline duration > 0.

Apply presentation reveal.

Expected:

- scientific track remains unchanged;
- presentation track is appended only when `(target_id, property_path)` is free;
- output duration is max(scientific duration, presentation duration);
- sampling scientific geometry at the same time yields the same scientific values as before presentation, except explicitly presentation-owned visual properties.

## F7 — Timeline Conflict

Input timeline already owns:

```text
science.line.path.trim_end
```

Presentation requests draw reveal for the same Polyline.

Expected first implementation:

- scientific track wins;
- presentation does not add a duplicate `trim_end` track;
- no generic additive blending is attempted;
- structured diagnostic/inspection record may report reveal conflict;
- resulting Timeline remains valid.

Second variant:

Input already owns:

```text
science.point.a.opacity
```

Fade reveal must likewise skip/conflict rather than replace science.

## F8 — Title and Time Annotation

Input animated Scene with duration 2 seconds.

Intent requests:

```text
title = "Reference Wave"
show_time = true
```

Expected:

- deterministic title ID, e.g. `presentation.title.primary`;
- deterministic time annotation ID `presentation.annotation.time`;
- title/text objects are presentation-owned;
- scientific primitive IDs untouched;
- time display may be static in Phase 1 if animated text is not yet supported, but implementation behavior must be explicit and deterministic;
- presentation labels do not affect scientific camera bounds unless policy explicitly says so.

## F9 — Basic Light Rig

Input one lit-capable context Surface.

`scientific_studio` expected resource roles:

```text
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Initial implementation may use fewer lights if preset table says so, but IDs and count must be deterministic.

Assertions:

- finite positive intensities;
- all are generic `Light` primitives;
- no Blender concepts/nodes in Scene;
- recomposition does not accumulate lights.

## F10 — Idempotent Recomposition

Take any non-empty fixture.

```text
base -> compose(intent A) -> scene A1
scene A1 -> compose(intent A) -> scene A2
```

Expected:

```text
A1 == A2
```

or, if exact dataclass equality is intentionally not used, equivalent deterministic primitive/material/timeline identity and values.

This is a mandatory Phase 1 gate.

## F11 — Preset Switch

```text
base
 -> analysis
 -> cinematic
```

Expected:

- scientific primitives unchanged throughout;
- obsolete `presentation.*` resources removed/replaced deterministically;
- no accumulating cameras/lights/labels;
- scientific Timeline preserved;
- only presentation-owned tracks/resources change.

First implementation may rebuild presentation resources instead of diffing them in place.

## F12 — Surface Without Quantitative Attributes

Input ordinary Surface with one color.

Intent requests ordinary analysis/publication styling only.

Expected:

- succeeds with current Scene v4;
- must not invent continuous scalar data or gradient colors.

If intent/context claims a required quantitative continuous surface colormap, expected result is a structured unsupported-capability diagnostic until visual attributes are implemented.

## F13 — PointCloud Existing Per-instance Colors

Input PointCloud with explicit `colors`.

Expected generic presentation behavior:

- colors remain scientific/view-owned data;
- presentation may add legend only if context explicitly supplies quantitative semantics/range;
- composer must not infer scalar values from RGB;
- color tuples are not rewritten merely to match theme if they encode data.

## F14 — Scientific Material Preservation

Input primitive references a scientific/view material.

Expected:

- presentation does not silently replace it unless policy explicitly owns style for that resource;
- quantitative/unlit color semantics preserved;
- presentation-owned materials use deterministic `presentation.material.*` IDs;
- no dangling material references.

## F15 — MemoryBackend Integration

For every Phase 1 fixture:

```text
compose -> BackendSession.open(MemoryBackend, scene) -> seek(...) -> close()
```

Expected:

- backend compatibility validation passes;
- all sampled Scenes remain valid;
- no Blender dependency/import.

## Golden semantic snapshots

Do not use screenshot golden tests for generic presentation Phase 1.

Preferred golden form is a compact canonical summary:

```text
primitive IDs + kinds
active camera ID
camera transform/projection
presentation light IDs/types
material IDs
Timeline target/property pairs
Timeline duration
```

A helper can later serialize this summary for stable fixture comparison.

Do not snapshot floating-point values at excessive precision if values are derived through trig; use mathematically justified tolerance where equality is not exact.

## Phase 1 required test list

Minimum tests:

```text
test_empty_scene_presentation_is_valid
test_fit_camera_uses_scene_local_bounds
test_nondefault_scene_frame_does_not_double_transform_camera
test_scientific_ids_are_preserved
test_presentation_ids_are_deterministic
test_recomposition_is_idempotent
test_existing_camera_preservation_policy
test_force_presentation_camera_keeps_scientific_camera
test_scientific_timeline_survives_presentation
test_reveal_conflict_does_not_override_scientific_track
test_preset_switch_does_not_accumulate_resources
test_required_quantitative_surface_color_reports_unsupported_without_attributes
test_memory_backend_accepts_composed_scene
```

## Native Blender follow-up fixtures

Only after generic tests are green:

- F3 camera framing;
- F6 scientific + reveal timeline;
- F9 light rig;
- F10 repeated composition/application;
- F11 preset switching;
- object/data-block identity for unchanged scientific primitives where incremental backend supports it;
- no Spectra-owned object/material leak.

## Success criterion

The first presentation runtime patch should be considered structurally successful when these fixtures show that premium presentation is deterministic, Scene-local, additive, idempotent, renderer-neutral, and incapable of silently overriding scientific geometry/time semantics.