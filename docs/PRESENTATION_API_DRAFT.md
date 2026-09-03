# Spectra Science — Presentation Runtime API Draft

Status: **design draft, not implemented runtime**.

This document converts `PREMIUM_PRESENTATION_SYSTEM.md` into a concrete Python-facing API shape that can be implemented after the current numerical runtime batch is validated green.

## Goal

The presentation API must transform a scientifically correct renderer-neutral `Scene` into a presentation-enriched `Scene` without changing scientific results or importing renderer SDKs.

Target flow:

```text
semantic value
  -> VisualizationRegistry.compile(...)
  -> base Scene
  -> compose_presentation(base_scene, intent, context)
  -> enriched Scene
  -> Blender / WebGPU / MemoryBackend / future renderer
```

The API should extend the existing `spectra.presentation` module rather than creating a competing presentation subsystem.

## Proposed module layout

```text
spectra/
  presentation.py                 existing helpers + top-level composer
  presentation_models.py          immutable value contracts
  presentation_presets.py         built-in presets
  presentation_color.py           range/color semantics
  presentation_layout.py          camera/axes/legend planning
```

This split is a draft. Keep public names stable even if private file organization changes.

## Core value types

Use frozen dataclasses or equivalent immutable value objects.

```python
from dataclasses import dataclass, field
from enum import Enum

class PresentationPreset(str, Enum):
    ANALYSIS = "analysis"
    PUBLICATION = "publication"
    PRESENTATION = "presentation"
    CINEMATIC = "cinematic"
    DARK_LAB = "dark_lab"

class CameraMode(str, Enum):
    FIT_ALL = "fit_all"
    FIT_PRIMARY = "fit_primary"
    ORTHOGRAPHIC_ANALYSIS = "orthographic_analysis"
    PERSPECTIVE_CONTEXT = "perspective_context"
    ORBIT_REVEAL = "orbit_reveal"
    FOLLOW_SUBJECT = "follow_subject"

class AnnotationDensity(str, Enum):
    NONE = "none"
    MINIMAL = "minimal"
    IMPORTANT_ONLY = "important_only"
    ANALYSIS = "analysis"
    TEACHING = "teaching"

class LightingMode(str, Enum):
    FLAT_ANALYSIS = "flat_analysis"
    SCIENTIFIC_STUDIO = "scientific_studio"
    SOFT_VOLUME_CONTEXT = "soft_volume_context"
    RIM_EMPHASIS = "rim_emphasis"
    UNLIT_DATA = "unlit_data"
```

Do not expose Blender concepts such as Eevee/Cycles, node group names, world-node sockets, or compositor settings in these types.

## Color-scale contract

```python
class ColorScaleKind(str, Enum):
    SEQUENTIAL = "sequential"
    DIVERGING = "diverging"
    CYCLIC = "cyclic"
    CATEGORICAL = "categorical"

class RangeMode(str, Enum):
    DATA = "data"
    EXPLICIT = "explicit"
    SYMMETRIC_ZERO = "symmetric_zero"
    ROBUST_PERCENTILE = "robust_percentile"

@dataclass(frozen=True)
class ColorScalePolicy:
    kind: ColorScaleKind
    palette: str
    range_mode: RangeMode = RangeMode.DATA
    minimum: float | None = None
    maximum: float | None = None
    center: float | None = None
    clamp: bool = True
    missing_value_label: str | None = None
```

Validation rules:

- explicit ranges require finite `minimum < maximum`;
- cyclic scales should not silently clamp a phase domain into a sequential interpretation;
- diverging scales should require an explicit or semantically justified center;
- presentation range must not alter source field values;
- units live with legend/quantity metadata, not as guessed strings in renderer code.

## Policy objects

```python
@dataclass(frozen=True)
class CameraPolicy:
    mode: CameraMode = CameraMode.FIT_ALL
    primary_id: str | None = None
    padding: float = 0.10
    orbit_degrees: float = 0.0
    follow_id: str | None = None

@dataclass(frozen=True)
class LegendPolicy:
    visible: bool = True
    compact: bool = False
    show_units: bool = True
    show_min_max: bool = True
    show_reference: bool = False

@dataclass(frozen=True)
class AxesPolicy:
    visible: bool = True
    grid: bool = False
    origin_marker: bool = False
    equal_scale: bool = False
    tick_density: str = "normal"

@dataclass(frozen=True)
class AnnotationPolicy:
    density: AnnotationDensity = AnnotationDensity.IMPORTANT_ONLY
    title: str | None = None
    subtitle: str | None = None
    show_time: bool = True
    show_provenance: bool = False

@dataclass(frozen=True)
class LightingPolicy:
    mode: LightingMode = LightingMode.SCIENTIFIC_STUDIO
    preserve_quantitative_colors: bool = True

@dataclass(frozen=True)
class AnimationPolicy:
    reveal: str = "none"
    reveal_duration: float = 0.6
    stagger: float = 0.12
    scientific_playback: bool = True
    camera_motion: bool = False

@dataclass(frozen=True)
class QualityPolicy:
    level: str = "interactive"
    display_glyph_limit: int | None = None
    display_surface_budget: int | None = None
    antialiasing_intent: str = "normal"
    allow_post_processing: bool = True
```

Any display limit must decimate only presentation geometry. It must never reduce numerical solver resolution or mutate source solutions.

## PresentationIntent

```python
@dataclass(frozen=True)
class PresentationIntent:
    preset: PresentationPreset = PresentationPreset.ANALYSIS
    camera: CameraPolicy | None = None
    color_scale: ColorScalePolicy | None = None
    legend: LegendPolicy | None = None
    axes: AxesPolicy | None = None
    annotations: AnnotationPolicy | None = None
    lighting: LightingPolicy | None = None
    animation: AnimationPolicy | None = None
    quality: QualityPolicy | None = None
    theme: str | None = None
```

Preset application should work as deterministic defaults plus explicit overrides:

```text
builtin preset defaults
        ↓
PresentationIntent explicit overrides
        ↓
validated resolved policy
```

Do not store a giant mutable dictionary of renderer options.

## Resolved presentation

Separate user intent from the fully resolved deterministic policy.

```python
@dataclass(frozen=True)
class ResolvedPresentation:
    preset: PresentationPreset
    camera: CameraPolicy
    legend: LegendPolicy
    axes: AxesPolicy
    annotations: AnnotationPolicy
    lighting: LightingPolicy
    animation: AnimationPolicy
    quality: QualityPolicy
    color_scale: ColorScalePolicy | None
    theme: str
```

Suggested API:

```python
def resolve_presentation(intent: PresentationIntent) -> ResolvedPresentation:
    ...
```

Pure resolution should not inspect Blender or mutate a Scene.

## Presentation context

The composer may need semantic metadata that is not safely inferred from raw geometry.

```python
@dataclass(frozen=True)
class QuantityPresentationMetadata:
    name: str
    unit_symbol: str | None = None
    quantity_kind: str | None = None
    signed: bool | None = None
    cyclic: bool = False
    non_negative: bool = False

@dataclass(frozen=True)
class PresentationContext:
    primary_primitive_id: str | None = None
    quantity: QuantityPresentationMetadata | None = None
    source_semantic_type: str | None = None
    result_fingerprint: str | None = None
```

The domain/view may supply this context. The presentation layer must not infer quantum phase, electric potential zero-centering, or coordinate meaning from object names.

## Composer API

Initial public shape:

```python
def compose_presentation(
    scene: Scene,
    intent: PresentationIntent,
    *,
    context: PresentationContext | None = None,
) -> Scene:
    ...
```

Requirements:

- input Scene remains unchanged;
- output scientific primitive IDs remain unchanged;
- presentation-owned resources use deterministic names from `PRESENTATION_RESOURCE_NAMESPACE.md`;
- repeated composition with the same inputs is deterministic;
- presentation changes do not recompute scientific domains;
- MemoryBackend must be able to inspect the result;
- no renderer SDK import.

## First implementation scope

Phase 1 should deliberately stay small:

1. policy dataclasses/enums;
2. preset resolution;
3. deterministic validation;
4. bounds-driven camera creation/replacement;
5. presentation-owned title/time labels;
6. existing `staggered_reveal` integration;
7. basic axes/light intent only if current Scene primitives express them cleanly.

Do not implement quantitative per-vertex colormaps, Geometry Nodes, compositor effects, or complex legend widgets in the first patch.

## Preset defaults

Suggested starting table:

```text
analysis:
  camera = orthographic_analysis when suitable, otherwise fit_all
  lighting = flat_analysis
  axes = visible
  annotations = analysis
  animation reveal = none

publication:
  camera = deterministic fit_all
  lighting = unlit_data or restrained
  axes = visible when quantitative
  annotations = minimal
  post = restricted

presentation:
  camera = fit_primary/fit_all
  lighting = scientific_studio
  annotations = teaching
  reveal = staggered

cinematic:
  camera = perspective_context/orbit_reveal
  lighting = scientific_studio or rim_emphasis
  annotations = important_only
  reveal = staged

dark_lab:
  theme = dark_lab
  camera = perspective_context
  lighting = rim_emphasis/scientific_studio
  annotations = important_only
```

Exact defaults may evolve before API stabilization.

## Backend capability negotiation draft

Do not put capability negotiation into Phase 1, but reserve a clean shape:

```python
@dataclass(frozen=True)
class PresentationBackendCapabilities:
    per_instance_color: bool = False
    volumetrics: bool = False
    post_processing: bool = False
    screen_space_labels: bool = False
    instanced_glyphs: bool = False
    camera_depth_of_field: bool = False
```

A later API may be:

```python
def resolve_for_backend(
    resolved: ResolvedPresentation,
    capabilities: PresentationBackendCapabilities,
) -> ResolvedPresentation:
    ...
```

Fallback must affect presentation quality only, never scientific semantics.

## Serialization stance

Do not modify `spectra.scene v4` merely to land Phase 1.

Preferred sequence:

1. implement in-process immutable contracts;
2. validate composer behavior;
3. decide whether presentation intent belongs in future `spectra.project` rather than Scene schema;
4. only version persistent schemas once the runtime contract proves stable.

## Testing plan after validation gate

Unit tests:

- preset resolution deterministic;
- explicit override wins;
- invalid color ranges rejected;
- input Scene not mutated;
- scientific IDs preserved;
- deterministic presentation IDs;
- same scene+intent produces equal output;
- changing presentation does not change source scientific geometry arrays;
- reveal timeline composes rather than replaces scientific timeline.

Integration tests:

- MemoryBackend inspection;
- electrostatic base Scene + analysis preset;
- Maxwell base Scene + cinematic preset;
- quantum phase view requests cyclic color semantics;
- Blender native mapping only after generic composer is green.

## Compatibility rule

Existing APIs remain valid:

```python
registry.compile_scene(value)
staggered_reveal(scene, ...)
```

Premium presentation is additive. Users should not be forced through presentation policies merely to obtain a scientific Scene.

## Success criterion

After implementation a caller should be able to write conceptually:

```python
scene = registry.compile_scene(solution_view)
scene = compose_presentation(
    scene,
    PresentationIntent(
        preset=PresentationPreset.CINEMATIC,
        annotations=AnnotationPolicy(
            density=AnnotationDensity.IMPORTANT_ONLY,
            title="Electromagnetic Wave",
        ),
    ),
    context=metadata,
)
backend.apply(scene.sample(0.0))
```

and no physics, PDE, chemistry, or quantum module should know that Blender may eventually render the result.