# Spectra Science — Presentation Runtime API Draft

Status: **design draft, not implemented runtime**.

This document converts `PREMIUM_PRESENTATION_SYSTEM.md` into a concrete Python-facing API shape that can be implemented after the current numerical runtime batch is validated green.

## Goal

The presentation API transforms a scientifically correct renderer-neutral `Scene` into a presentation-enriched `Scene` without changing scientific results or importing renderer SDKs.

```text
semantic value
  -> VisualizationRegistry.compile(...)
  -> base Scene
  -> compose_presentation(base_scene, intent, context)
  -> enriched Scene
  -> Blender / WebGPU / MemoryBackend / future renderer
```

The API extends existing `spectra.presentation` rather than creating a parallel presentation engine.

## Current Core feasibility

Source review confirms current Core already provides enough generic infrastructure for Phase 1:

```text
Camera: perspective + orthographic
Transform3D.look_at(...)
scene_bounds(...)
TextLabel
Light
Material
Scene.active_camera_id
immutable Scene
Timeline
merge_timelines(...)
staggered_reveal(...)
```

Therefore Phase 1 does not need a Scene schema change.

Important current limitations:

- no first-class generic background/world resource;
- no screen-space label contract;
- `Surface` has one uniform color and no per-vertex scalar/color channel;
- advanced quantitative colorbars are not directly representable yet.

See `PRESENTATION_CORE_FEASIBILITY_AUDIT.md` and `VISUAL_ATTRIBUTE_MODEL.md`.

## Proposed module layout

```text
spectra/
  presentation.py                 existing helpers + top-level composer
  presentation_models.py          immutable value contracts
  presentation_presets.py         built-in presets
  presentation_color.py           later quantitative range/color semantics
  presentation_layout.py          camera/axes/legend helpers as needed
```

Private file layout may evolve; public contracts should stabilize only after tests.

## Core value types

Use frozen dataclasses or equivalent immutable value objects.

```python
from dataclasses import dataclass
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

Do not expose Blender concepts such as Eevee/Cycles, node groups, compositor nodes, or Blender world settings in these types.

## Color-scale contract

Quantitative color work is a later package, but the API direction is:

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

Rules:

- explicit ranges require finite `minimum < maximum`;
- cyclic data must not silently become sequential;
- diverging scales require a meaningful center;
- display mapping never changes source field values;
- units come from semantic/view metadata, not renderer guesses.

See `SCIENTIFIC_COLOR_POLICY.md`.

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

Display budgets may reduce presentation sampling only. They must never change solver resolution/precision.

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

Resolution order:

```text
built-in preset defaults
        ↓
explicit PresentationIntent overrides
        ↓
validated ResolvedPresentation
```

## ResolvedPresentation

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

Pure API:

```python
def resolve_presentation(intent: PresentationIntent) -> ResolvedPresentation:
    ...
```

It must not inspect Blender or mutate a Scene.

## Presentation context

Semantic metadata not safely inferable from geometry is explicit:

```python
@dataclass(frozen=True)
class QuantityPresentationMetadata:
    name: str
    unit_symbol: str | None = None
    quantity_kind: str | None = None
    signed: bool | None = None
    cyclic: bool = False
    non_negative: bool = False
    meaningful_center: float | None = None
    preferred_color_role: str | None = None

@dataclass(frozen=True)
class PresentationContext:
    primary_primitive_id: str | None = None
    quantity: QuantityPresentationMetadata | None = None
    source_semantic_type: str | None = None
    result_fingerprint: str | None = None
```

Domains/views may supply this metadata. Presentation must not infer quantum phase or electric-potential reference semantics from IDs/names.

## Composer API

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

- input Scene unchanged;
- scientific primitive IDs unchanged;
- presentation IDs deterministic/namespaced;
- repeated composition deterministic;
- no scientific recomputation;
- MemoryBackend can inspect result;
- no renderer SDK import.

## Phase 1 implementation scope

Implement only features cleanly expressible by current generic Scene:

1. policy dataclasses/enums;
2. preset resolution;
3. validation;
4. bounds-driven camera creation/replacement;
5. active-camera assignment;
6. title/subtitle/time `TextLabel` resources;
7. existing reveal/timeline composition;
8. basic generic `Light` rig where appropriate.

Current source proves these are feasible without Core schema changes.

## Camera implementation direction

Use current:

```text
scene_bounds(...)
Bounds3D.center
Bounds3D.bounding_sphere_radius
Transform3D.look_at(...)
Camera(projection=...)
```

A presentation-private helper can derive deterministic eye position/distance from bounds and FOV.

Do not add Blender lens settings to generic policy.

## Theme/background stance

Current Scene has no generic world/background field.

Therefore Phase 1 `theme` may influence currently expressible resources such as:

- label colors;
- presentation materials;
- lights;

but actual world/background realization is deferred.

Do not add `Scene.background` casually.

If multiple renderers need a persistent generic environment intent, introduce it in its own checkpoint.

## Axes and legend stance

No dedicated Axes or Legend primitive currently exists.

Basic axes/legends may be composed from:

```text
Polyline
TextLabel
Region
Group
```

Advanced ticks/layout/quantitative colorbars are later presentation utilities.

## Backend capability negotiation

**Do not create a separate presentation/renderer capability registry.**

Spectra already has:

```python
spectra.backends.base.BackendCapabilities
```

Premium presentation must extend/use this existing single source of backend capability truth.

Later pure resolution:

```python
def resolve_presentation_for_backend(
    resolved: ResolvedPresentation,
    capabilities: BackendCapabilities,
) -> BackendResolvedPresentation:
    ...
```

See `RENDERER_CAPABILITIES_API_DRAFT.md`.

Do not extend `BackendCapabilities` in Phase 1 unless generic presentation actually needs negotiation. Add the smallest fields later with conservative defaults.

## Current Blender source facts

Current reference Blender backend already maps:

```text
Camera
Light
TextLabel
Material
PointCloud
VectorGlyphSet
Surface
```

PointCloud/VectorGlyphSet per-instance colors use a bounded material-slot path with at most 256 unique colors per primitive. That is not yet a high-cardinality quantitative attribute path.

Current Surface has one uniform generic color.

Therefore quantitative surface color is explicitly deferred to the visual-attribute work package.

## Serialization stance

Do not modify `spectra.scene v4` for Phase 1.

Preferred sequence:

1. implement in-process presentation contracts;
2. validate composer behavior;
3. store durable presentation intent later in `spectra.project` if appropriate;
4. version Scene only if a genuinely generic primitive/resource extension requires it.

## Preset defaults

Initial family:

```text
analysis
publication
presentation
cinematic
dark_lab
```

Keep differences strong and limited.

Conceptually:

```text
analysis:
  deterministic analytical framing
  flat/unlit data emphasis
  axes/diagnostics visible
  no reveal by default

publication:
  deterministic restrained framing
  minimal annotations
  quantitative integrity prioritized

presentation:
  teaching annotations
  staged reveal
  scientific-studio lighting

cinematic:
  perspective context
  important-only annotations
  controlled lighting/camera motion

dark_lab:
  dark-style presentation resources where expressible
  luminous bounded accents
  high contrast labels
```

## Tests after validation gate

Unit:

- preset resolution deterministic;
- explicit override wins;
- invalid policies rejected;
- policy objects immutable.

Composer:

- input Scene unchanged;
- scientific IDs preserved;
- scientific geometry arrays unchanged;
- deterministic presentation IDs;
- timeline merged, not replaced;
- fit camera active and valid;
- repeated composition equal;
- MemoryBackend compatible.

Integration:

- Maxwell base Scene + cinematic preset first;
- electrostatic analysis/dark_lab next;
- Blender native mapping only after generic composer is green.

## Compatibility rule

Existing flows remain valid:

```python
registry.compile_scene(value)
staggered_reveal(scene, ...)
```

Premium presentation is additive.

## Success criterion

A caller can conceptually write:

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

and no physics, PDE, chemistry, quantum, or Blender-specific code is required in the presentation composer.