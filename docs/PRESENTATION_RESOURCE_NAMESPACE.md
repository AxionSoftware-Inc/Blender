# Spectra Science — Presentation Resource Namespace and Ownership

This document defines deterministic naming/ownership rules for presentation resources added around a scientific Scene.

The goal is to preserve incremental updates, cleanup safety, preset switching, and cross-backend reproducibility.

## Why deterministic IDs matter

Presentation enrichment may add:

- cameras;
- lights;
- legends;
- axes;
- labels;
- titles;
- scale bars;
- background/context primitives;
- annotation groups;
- presentation animation tracks.

If these resources receive random/native-generated identities, switching presets or scrubbing animation can create duplicates and break incremental backends.

## Scientific IDs vs presentation IDs

Scientific primitive IDs belong to the semantic/view compiler.

Examples:

```text
field.velocity.arrows
trajectory.particle_001
surface.temperature.slice_z
solid.deformed_nodes
```

Presentation enrichment should normally preserve those IDs.

Presentation-owned resources use a reserved namespace:

```text
presentation.*
```

A presentation composer must not rename scientific primitives merely to style them.

## Recommended top-level namespaces

```text
presentation.camera.*
presentation.light.*
presentation.legend.*
presentation.axes.*
presentation.annotation.*
presentation.title.*
presentation.scale.*
presentation.context.*
presentation.group.*
presentation.track.*
```

Examples:

```text
presentation.camera.primary
presentation.camera.compare.left
presentation.light.key
presentation.light.fill
presentation.light.rim
presentation.legend.temperature
presentation.legend.vector_scale
presentation.axes.world
presentation.annotation.time
presentation.annotation.parameter.reynolds
presentation.title.primary
presentation.scale.length
```

## Variant scoping

A project may hold several presentation variants.

Conceptually:

```text
analysis
publication
cinematic
```

Persistent configuration identifies the variant, but Scene primitive IDs should remain deterministic inside one compiled variant.

Do not prefix every scientific primitive with the preset name. Scientific geometry should remain reusable.

Presentation-owned resources may optionally include a variant namespace when multiple variants coexist in one Scene graph:

```text
presentation.variant.cinematic.camera.primary
```

If only one variant is instantiated at a time, the simpler namespace is preferred.

## Semantic resource key

A presentation resource should be identifiable by a semantic key, not renderer-native datablock name.

Conceptually:

```text
PresentationResourceKey(
    category="legend",
    role="temperature",
    instance="primary",
)
```

The deterministic Scene ID can then derive from this key.

## Backend-native names

A Blender backend may derive native names such as:

```text
Spectra__presentation__legend__temperature
```

but this is backend implementation detail.

Scientific/project code should never depend on the Blender object name.

## Ownership metadata

Every renderer-owned Spectra resource should be distinguishable from user content.

A backend may use:

- a dedicated collection;
- object custom properties;
- datablock metadata;
- an internal ownership table;
- deterministic prefixes plus explicit owner IDs.

Preferred conceptual metadata:

```text
spectra.owner = <session/project id>
spectra.semantic_id = <Scene primitive/resource id>
spectra.kind = presentation|scientific
```

The exact native mechanism is backend-specific.

## Cleanup rule

Cleanup may remove only resources owned by the current Spectra session/project unless the user explicitly requests broader cleanup.

Do not delete:

- user cameras;
- user materials;
- user lights;
- unrelated node groups;
- unrelated compositor nodes;
- objects merely because their name resembles a Spectra name.

Ownership must be explicit enough to avoid name-only destructive cleanup.

## Stable update rule

When the presentation resource role is unchanged, update in place where practical.

Examples:

```text
camera.primary transform changed -> same camera object
legend.temperature range changed -> same legend group when structure compatible
annotation.time text changed -> same text object
light.key energy changed -> same light object
```

A rebuild is acceptable when representation structure changes.

## Preset switching

Switching:

```text
analysis -> cinematic
```

should compute a resource diff.

Conceptually:

```text
shared resources -> update
obsolete resources -> remove
new resources -> create
scientific primitives -> preserve
```

Do not destroy/recreate the entire Scene by default.

## Presentation animation tracks

Presentation tracks should use deterministic track identifiers derived from target/resource role where the timeline model supports IDs.

Conceptual names:

```text
presentation.track.reveal.field_lines
presentation.track.camera.primary.orbit
presentation.track.annotation.time.fade
```

Scientific and presentation tracks must remain distinguishable for inspection/debugging.

## Legend IDs

One quantitative legend per semantic scale role should have a deterministic ID.

Examples:

```text
presentation.legend.temperature
presentation.legend.pressure_delta
presentation.legend.phase
presentation.legend.probability_density
```

If two views intentionally use different ranges for the same quantity, disambiguate explicitly:

```text
presentation.legend.temperature.left
presentation.legend.temperature.right
```

Do not silently create duplicate legends with random suffixes.

## Axes IDs

Axes should identify the displayed frame/view:

```text
presentation.axes.world
presentation.axes.slice_xy
presentation.axes.projected_geodesic
```

This matters because projected scientific views may not share the original coordinate semantics.

## Annotation IDs

Annotations should be semantically addressable:

```text
presentation.annotation.time
presentation.annotation.solver
presentation.annotation.cfl
presentation.annotation.energy_error
presentation.annotation.selected_particle
```

This supports incremental text/value updates.

## Material ownership

Presentation may request material roles, but renderer material datablocks should be shared where safe.

Conceptual roles:

```text
presentation.material.data_unlit
presentation.material.context_translucent
presentation.material.annotation
```

Quantitative data material instances may need scale/palette-specific parameters.

Avoid creating one material datablock per sample/glyph.

## Shared resources

Some presentation resources may be shared across primitives:

- one palette/material configuration;
- one world/background setup;
- one light rig;
- one font style role;
- one legend scale.

A backend should track reference/ownership safely so deleting one primitive does not remove a resource still in use.

## Project/session boundaries

Two Spectra projects coexisting in one Blender file must not own each other's resources.

Future ownership may include:

```text
project_id
presentation_variant_id
backend_session_id
```

The minimum rule is that cleanup can unambiguously determine whether a native resource belongs to the current active Spectra context.

## Serialization

Renderer-neutral Scene/project serialization should preserve semantic/presentation IDs, not backend-generated native names.

This allows another renderer to reconstruct equivalent resources.

## Debugging

A future inspector should be able to answer:

```text
Which Spectra semantic/presentation resource created this Blender object?
Which project owns it?
Which presentation preset/policy created it?
Is it safe to remove/rebuild?
```

Deterministic IDs and ownership metadata make this possible.

## Success criterion

Repeated presentation composition, preset switching, animation scrubbing, and renderer-session recreation should converge on the same semantic resource identities rather than accumulating duplicate cameras, lights, legends, materials, or annotations.
