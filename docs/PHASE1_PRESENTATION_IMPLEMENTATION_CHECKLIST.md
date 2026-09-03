# Spectra Science — Phase 1 Presentation Implementation Checklist

Status: **implementation plan, not yet runtime code**.

This checklist is the exact first product-runtime slice to execute after the pending numerical/experiments validation becomes green.

It narrows the broader presentation architecture into a small reviewable patch set.

## Gate before starting

Do not begin this runtime phase until the current executable batch through:

```text
00b5403a9ffb005b7eb011833174e013158ee1f4
```

has a new full green baseline.

Record:

```text
final validated SHA
compileall status
pytest count
DomainCatalog domain/provider count
root fixes if any
```

Documentation-only commits after `00b5403...` do not change this gate.

## Phase 1 objective

Implement renderer-neutral presentation semantics and a minimal presentation composer without changing scientific domains, Scene schema, or Blender backend internals.

Target:

```text
base Scene
+ PresentationIntent
    -> deterministic presentation-enriched Scene
```

## Expected files

Recommended first patch:

```text
spectra/presentation_models.py      new
spectra/presentation_presets.py     new
spectra/presentation.py             extend existing module
spectra/__init__.py                 only if public exports belong there

tests/test_presentation_models.py   new
tests/test_presentation_composer.py new
```

Avoid changing:

```text
spectra/core/scene.py
spectra/core/serialization.py
spectra/backends/blender/*
spectra/domains/*
spectra/numerics.py
```

unless implementation reveals a genuinely universal missing contract.

## Runtime types to implement first

From `PRESENTATION_API_DRAFT.md`:

```text
PresentationPreset
CameraMode
AnnotationDensity
LightingMode
CameraPolicy
LegendPolicy
AxesPolicy
AnnotationPolicy
LightingPolicy
AnimationPolicy
QualityPolicy
PresentationIntent
ResolvedPresentation
PresentationContext
QuantityPresentationMetadata
```

`ColorScalePolicy` may be represented but quantitative color application can remain Phase 2/3 if it would force Scene/material schema changes.

## Required built-in presets

Exactly five initial preset names:

```text
analysis
publication
presentation
cinematic
dark_lab
```

Keep defaults explicit in one module.

Do not create dozens of style presets in Phase 1.

## Required functions

```python
def resolve_presentation(
    intent: PresentationIntent,
) -> ResolvedPresentation:
    ...


def compose_presentation(
    scene: Scene,
    intent: PresentationIntent,
    *,
    context: PresentationContext | None = None,
) -> Scene:
    ...
```

Existing functions remain valid:

```python
merge_timelines(...)
staggered_reveal(...)
```

## Composer features allowed in Phase 1

Implement only features already expressible cleanly with generic Scene primitives/resources.

### 1. Preset resolution

Deterministic defaults + explicit override.

### 2. Camera planning

Use existing Scene bounds/camera infrastructure if sufficient.

Minimum:

```text
fit_all
perspective_context
orthographic_analysis only if generic Camera supports it cleanly
```

Do not add renderer-specific focal-length logic.

### 3. Title/time annotation

Use `TextLabel` if current primitive semantics are sufficient.

Presentation IDs:

```text
presentation.annotation.title
presentation.annotation.subtitle
presentation.annotation.time
```

### 4. Reveal timeline

Compose with current scientific timeline through existing helpers.

Scientific time must not be overwritten.

### 5. Generic light intent

Only add generic `Light` primitives when semantics are already expressible.

Do not encode Blender world/node/compositor state.

## Explicitly deferred

Do not put these into the first patch:

- Blender nodes;
- Cycles/Eevee configuration;
- Geometry Nodes;
- volumetric effects;
- per-vertex/per-instance quantitative color attributes if Scene lacks a clean contract;
- complex axes/ticks system;
- publication report exporter;
- project persistence;
- plugin presentation extensions;
- WebGPU capability negotiation;
- Scene schema v5.

## Immutability rules

`PresentationIntent` and policy objects should be immutable/frozen.

`compose_presentation()` should return a new `Scene`.

It must not mutate:

- the input Scene;
- semantic solution objects;
- domain registry;
- numerical results.

## Stable ID rules

Scientific IDs must stay exactly the same.

Presentation-owned IDs follow `PRESENTATION_RESOURCE_NAMESPACE.md`.

Repeated composition with identical inputs should generate the same IDs.

Changing a title must not rename/recreate scientific primitives.

## Timeline rules

Distinguish:

```text
scientific tracks
presentation tracks
```

The composer merges them.

It must not:

- rescale simulation time silently;
- remove existing tracks;
- change numerical sample times;
- reinterpret Blender frames as scientific truth.

## Validation rules

Reject early:

- negative camera padding;
- negative reveal duration/stagger;
- follow/primary IDs that are required by a selected mode but absent;
- invalid enum/string identifiers;
- non-finite numeric presentation parameters.

Use ordinary `ValueError` initially if a new structured diagnostic subsystem is not yet implemented. Do not introduce the entire future diagnostics platform just for this phase.

## Unit tests

### `test_presentation_models.py`

Must cover:

- frozen/immutable policy objects;
- default `PresentationIntent`;
- each built-in preset resolves;
- explicit overrides win over preset defaults;
- invalid values rejected;
- deterministic equality/hash behavior where applicable.

### `test_presentation_composer.py`

Use a small generic Scene with at least:

```text
Polyline
Surface or PointCloud
existing Timeline
```

Assert:

- input Scene unchanged;
- scientific primitive IDs unchanged;
- title gets deterministic presentation ID;
- presentation timeline composes with scientific timeline;
- repeated composition is deterministic;
- analysis vs cinematic produce intentionally different presentation resources;
- no scientific vertex/point arrays change merely due to preset change.

## MemoryBackend integration

One test should apply/sample the enriched Scene through MemoryBackend or current backend-neutral session flow.

Purpose:

- prove presentation remains renderer-independent;
- catch unsupported generic primitives before Blender work.

## Canonical proof scene

Use exactly one initial proof scenario after unit tests:

```text
Maxwell E/B base Scene
```

Why:

- already has animated generic vector content;
- Blender native vector update path is previously verified;
- presentation can add title/camera/reveal without touching EM computation.

Phase 1 does not need Blender execution unless generic Scene behavior changed in a way that warrants a targeted smoke.

## Public exports

Do not immediately export every internal policy helper from root `spectra`.

Preferred provisional import:

```python
from spectra.presentation_models import PresentationIntent, PresentationPreset
from spectra.presentation import compose_presentation
```

After the API proves stable, `spectra.sdk` can curate public exports.

## Documentation update required with implementation

When Phase 1 lands:

- update `CURRENT_STATUS.md`;
- mark presentation semantics/composer as implemented-awaiting-validation or verified depending on checkpoint;
- do not mark Blender premium presentation implemented;
- update `PREMIUM_PRESENTATION_SYSTEM.md` implementation-status section.

## Exit gate

Before Phase 2:

```text
python -m compileall spectra
pytest -q
```

must be green.

No need for full 10k Blender benchmark because Blender backend is not modified.

If generic Camera/Light/Timeline Scene behavior changed materially, run a small targeted Blender smoke only.

## Phase 2 only after gate

Then proceed to:

```text
quantitative color scales
legends
axes/basic scale references
quantity/unit metadata presentation
```

Do not stack Blender premium adapter in the same unchecked patch.

## Success criterion

At the end of Phase 1 this code should be possible without changing a scientific domain:

```python
base = registry.compile_scene(maxwell_view)
shown = compose_presentation(
    base,
    PresentationIntent(preset=PresentationPreset.CINEMATIC),
)
```

and `shown` should remain a completely renderer-neutral Spectra `Scene`.