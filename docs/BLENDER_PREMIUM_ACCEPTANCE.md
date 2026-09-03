# Spectra Science — Blender Premium Acceptance Checklist

This document defines acceptance criteria for the future Blender premium-presentation implementation.

It is intentionally a validation checklist, not a request to implement Blender-specific presentation before the current numerical milestone is green.

## Purpose

A premium Blender scene is acceptable only if it satisfies three independent requirements:

1. scientific correctness is preserved;
2. Spectra architecture boundaries remain intact;
3. the resulting scene is visually coherent and production-oriented.

Visual quality alone is not sufficient.

## Gate A — architecture

Required:

- no `bpy` imports in Core or scientific domains;
- presentation semantics remain renderer-neutral;
- Blender adapter consumes generic Scene/presentation intent;
- scientific formulas are not duplicated in backend code;
- scientific time remains owned by Spectra;
- presentation changes do not recompute scientific solutions;
- renderer fallback does not change scientific meaning;
- stable Spectra primitive IDs remain stable when only presentation styling changes.

Reject the implementation if premium styling requires domain-specific Blender branches such as:

```text
if quantum: create blender shader X
if cfd: create blender node group Y
```

Those decisions belong in generic view/presentation semantics plus backend interpretation.

## Gate B — ownership and cleanup

Every native presentation resource created by Spectra must have deterministic ownership.

Validate:

- camera objects;
- lights;
- world resources created/modified by Spectra;
- materials;
- node groups;
- Geometry Nodes groups;
- text objects;
- legend geometry;
- compositor resources if created;
- presentation collections.

`destroy()` or equivalent cleanup must remove Spectra-owned resources without deleting unrelated user scene content.

Repeated create/apply/destroy cycles must not monotonically leak Blender datablocks.

## Gate C — incremental behavior

Changing scientific time or presentation parameters should not unnecessarily recreate native geometry.

For topology-stable content validate identity preservation for:

- PointCloud mesh;
- Polyline curve;
- Surface mesh;
- VectorGlyphSet representation;
- camera object;
- presentation lights;
- legend/axes groups where structure is unchanged.

Examples of acceptable rebuild triggers:

- topology changes;
- representation type changes;
- preset changes that structurally require another native technique.

Examples of unacceptable rebuild triggers:

- scalar values changed but topology did not;
- camera moved;
- time label changed;
- material parameter changed;
- glyph vectors changed with the same glyph count.

## Gate D — quantitative color integrity

For scenes using scientific color maps:

- one explicit data range drives both visual mapping and legend;
- range/center/clamp policy is inspectable;
- zero-centered diverging scales remain centered correctly;
- cyclic phase scales wrap continuously;
- values outside clamp range follow declared behavior;
- NaN/missing data follows declared behavior;
- lighting does not arbitrarily shift quantitative colors in analysis/publication modes;
- screen/render output matches legend semantics within expected renderer color-management behavior.

Never auto-normalize each animation frame independently unless the presentation policy explicitly requests per-frame normalization and warns that cross-time comparison is lost.

## Gate E — camera and framing

Validate each canonical scenario with at least:

- `analysis`;
- `publication`;
- `presentation`;
- `cinematic`.

Checks:

- main content is inside frame;
- no important content is clipped;
- camera fit is deterministic for publication mode;
- legends do not cover the primary scientific signal;
- orthographic mode preserves scale where requested;
- perspective presets retain comprehensible geometry;
- animation camera moves do not fight scientific-time motion.

## Gate F — lighting

Validate:

- primary structure remains readable;
- quantitative unlit data is not distorted by decorative lights;
- context geometry remains distinguishable from data geometry;
- dark presets do not crush low-valued scientific content;
- rim/bloom/emission effects do not become the only encoding of magnitude/category;
- transparent context does not create misleading depth ordering.

## Gate G — labels, legends, and axes

Required:

- units come from semantic/presentation metadata rather than guessed strings;
- time indicator reflects Spectra engine time;
- axis labels reflect the displayed coordinate semantics;
- projected relativity/manifold views do not label projected coordinates as original higher-dimensional coordinates unless true;
- legends remain readable in target render resolution;
- text does not flicker/rebuild unnecessarily across animation frames;
- large labels do not dominate cinematic scenes;
- publication mode preserves quantitative interpretation.

## Gate H — dense data

Premium rendering must preserve the existing batching rule.

Target representations:

```text
10k particles       -> O(1) native object count
10k vector glyphs   -> O(1) native object count
large scalar field  -> batched mesh/attribute/volume representation
```

Reject any premium implementation that improves appearance by expanding dense scientific data into one Blender object per sample.

Geometry Nodes or attributes are encouraged when they improve scale, but are not mandatory for the first premium milestone.

## Gate I — animation

Validate separately:

### Scientific animation

- wave evolution;
- Maxwell E/B evolution;
- particle trajectory;
- deforming solid;
- time-dependent scalar surface/slice.

### Presentation animation

- reveal;
- camera transition;
- label appearance;
- highlight/focus;
- hold/pause.

Combined animation must preserve scientific time semantics.

No object-count or datablock leak during repeated frame scrub.

## Gate J — canonical scenes

Minimum premium acceptance suite should eventually include:

1. electrostatic field laboratory;
2. Maxwell wave;
3. quantum probability + phase;
4. CFD flow/vorticity;
5. thermoelastic deformation;
6. reaction-diffusion;
7. Schwarzschild/geodesic scene;
8. experiment/convergence/Pareto scene.

Each scenario should have a known presentation intent and expected interpretation criteria from `SHOWCASE_SCENARIOS.md`.

## Gate K — preset switching

Given one base scientific Scene:

```text
analysis -> publication -> cinematic -> analysis
```

should not:

- recompute science;
- lose scientific primitive identity;
- duplicate presentation resources;
- accumulate materials/lights/cameras;
- mutate the saved base Scene destructively.

Preset-specific resources should use deterministic ownership/namespace rules.

## Gate L — save/reload

Before calling the premium backend production-ready, test:

- save `.blend`;
- close/reopen;
- identify Spectra-owned objects/resources;
- continue timeline updates where supported;
- reapply presentation intent;
- clean up without removing user content.

This can be later than the first premium prototype but is required before broad user release.

## Gate M — render modes

At minimum test:

- viewport/interactive path used by development;
- final still render;
- animation render.

If multiple Blender render engines are supported, capability negotiation should be explicit. Do not silently assume a compositor/shader feature exists everywhere.

## Gate N — performance reporting

Separate measurements:

- base Scene compile;
- presentation composition;
- Blender native create;
- first apply;
- repeated incremental update;
- preset switch;
- frame scrub;
- final render time where relevant.

Do not combine solver runtime with renderer runtime in one ambiguous number.

## Gate O — visual review rubric

For every canonical premium scene score:

- scientific clarity;
- hierarchy;
- color interpretability;
- depth/readability;
- annotation quality;
- camera composition;
- motion quality;
- consistency with other Spectra scenes;
- accessibility;
- unnecessary decoration.

A scene may be technically correct and still fail premium review if users cannot immediately see the intended scientific structure.

## Initial premium milestone

The first implementation does not need every advanced Blender feature.

A strong first milestone is:

- deterministic themes;
- auto-fit camera;
- studio/analysis lighting;
- quantitative colors + legends;
- axes/time/title labels;
- reveal animation;
- stable incremental native objects;
- five canonical showcase scenes.

Advanced later work may include:

- Geometry Nodes glyph instancing;
- volumetrics;
- screen-space labels;
- advanced compositor treatment;
- depth-of-field policies;
- large-data LOD.

## Success criterion

A premium Blender adapter is successful when the same scientific Scene can switch presentation styles and animate at high visual quality without changing scientific semantics, leaking resources, or returning to a one-object-per-sample Blender architecture.
