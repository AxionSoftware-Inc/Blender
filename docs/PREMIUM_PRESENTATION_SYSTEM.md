# Spectra Science — Premium Presentation System

This document defines the presentation layer that turns a scientifically correct Spectra `Scene` into a polished scientific communication scene without moving scientific meaning into Blender, WebGPU, Unreal, or another renderer.

## Goal

The desired product flow is:

```text
scientific intent
    -> domain semantics
    -> computation / field / trajectory / solution
    -> semantic visualization compiler
    -> base Scene + Timeline
    -> presentation policy
    -> presentation-enriched Scene + Timeline
    -> renderer backend
```

The presentation layer answers **how to communicate the result clearly and attractively**. It must not change the numerical solution or invent scientific meaning.

The same presentation intent should remain useful with Blender, WebGPU, a headless renderer, a saved Scene document, or a future backend.

## Existing foundation

Spectra already has two distinct pieces that this system should extend rather than replace:

- `VisualizationRegistry`: type-directed semantic object -> renderer-neutral `Scene` compilation;
- `spectra.presentation`: renderer-neutral timeline helpers such as staggered reveal and timeline composition.

Premium presentation should sit after semantic visualization and before the renderer backend.

## Separation of responsibilities

### Scientific domain

Owns:

- semantic quantities and fields;
- formulas and physical meaning;
- explicit visualization semantics when no canonical view exists;
- meaningful units and labels;
- mathematically valid sampling choices or constraints.

Does not own:

- Blender materials;
- render engines;
- node names;
- compositor graphs;
- camera focal lengths specific to a renderer;
- cinematic presets.

### Visualization compiler

Owns:

- mapping semantics into generic primitives;
- topology and sampling needed to communicate the scientific object;
- stable primitive IDs;
- renderer-independent color/size intent when scientifically meaningful.

Examples:

```text
Trajectory -> Polyline + moving Point
VectorField3D sample -> VectorGlyphSet
Scalar slice -> Surface
Experiment response -> Polyline / PointCloud / labels
```

### Presentation policy

Owns communication choices such as:

- scene framing;
- camera composition intent;
- background/theme;
- typography hierarchy;
- color-map intent;
- legends and scales;
- axes/grid presentation;
- annotation density;
- reveal order;
- animation pacing;
- visual emphasis;
- lighting intent;
- quality/performance tradeoff.

### Renderer backend

Owns native implementation of presentation intent:

- native materials/shaders;
- lights;
- compositor/post-processing where supported;
- renderer-specific anti-aliasing;
- native text/font objects;
- native camera settings;
- GPU/Geometry Nodes implementation details.

A renderer may degrade gracefully when it cannot express a presentation feature, but it must not change scientific semantics.

## Presentation intent model

The future runtime API should prefer explicit immutable presentation intent rather than renderer-specific option dictionaries.

Conceptual types:

```text
PresentationPreset
PresentationTheme
CameraPolicy
LightingPolicy
ColorScalePolicy
LegendPolicy
AxesPolicy
AnnotationPolicy
AnimationPolicy
QualityPolicy
```

A composed presentation request may conceptually look like:

```text
PresentationIntent(
    preset="cinematic",
    theme="dark_lab",
    camera="auto_fit_orbit",
    lighting="scientific_studio",
    color_scale="diverging_zero_centered",
    legend="compact",
    annotations="important_only",
    animation="explain_then_evolve",
    quality="high",
)
```

These names are semantic policy identifiers, not Blender configuration names.

## Built-in preset families

Initial presets should be deliberately few and strongly differentiated.

### `analysis`

Purpose: inspect data and numerical behavior.

Characteristics:

- neutral background;
- high information density;
- visible axes/units;
- minimal decorative lighting;
- explicit legends and scales;
- fast interaction prioritized over cinematic quality.

### `publication`

Purpose: paper/report figure.

Characteristics:

- clean light or transparent background;
- restrained typography;
- high contrast and accessible palette;
- exact units and scale bars;
- minimal perspective distortion where appropriate;
- deterministic framing.

### `presentation`

Purpose: slides/lesson/demo.

Characteristics:

- larger labels;
- simplified legends;
- stronger hierarchy;
- staged reveal;
- moderate motion;
- camera chosen for immediate comprehension.

### `cinematic`

Purpose: premium demo/video/marketing visualization.

Characteristics:

- controlled dark or atmospheric background;
- depth-enhancing lighting;
- smooth camera transitions;
- progressive reveal;
- lower annotation density;
- emphasis on silhouette, motion, and structure;
- renderer-specific post effects allowed only as backend interpretation.

### `dark_lab`

Purpose: high-tech scientific dashboard/demo style.

Characteristics:

- dark neutral environment;
- luminous but bounded data emphasis;
- clear bright labels;
- strong depth cues;
- no meaning encoded only through glow.

Presets should be composable overrides rather than giant renderer-specific scene templates.

## Camera policy

Automatic camera behavior must be based on generic scene bounds and semantic intent.

Useful policies:

- `fit_all`: frame all visible scientific content;
- `fit_primary`: frame an explicitly identified primary group/object;
- `orthographic_analysis`: reduce perspective distortion;
- `perspective_context`: retain spatial depth;
- `orbit_reveal`: slow deterministic orbit around stable bounds;
- `follow_subject`: follow a moving particle/feature while retaining context;
- `split_compare`: coordinated views for before/after or solver comparison.

Camera fitting should use Spectra bounds/coordinate semantics. The backend converts the generic camera intent to native settings.

The presentation layer must never infer a scientifically privileged axis unless the semantic visualization or user request identifies one.

## Color policy

Color is a scientific communication channel, not decoration only.

The presentation system should distinguish:

- categorical palettes;
- sequential scalar palettes;
- diverging palettes;
- cyclic palettes for phase/angle;
- signed vector/scalar emphasis;
- uncertainty/confidence styling;
- selection/highlight colors.

A color scale should carry semantic metadata:

```text
quantity / metric name
unit
range policy
center policy
clamp policy
missing-data policy
color-map identifier
legend requirement
```

Examples:

- temperature: sequential unless comparison around a meaningful reference is requested;
- electric potential: often diverging around zero when the data/range supports it;
- quantum phase: cyclic;
- probability density: non-negative sequential;
- pressure difference: diverging when centered on reference pressure.

The renderer should not independently choose a color map for a scientific quantity.

## Legend and annotation policy

Legends and labels should be Scene content or renderer-neutral presentation resources whenever possible.

Useful annotation classes:

- title/subtitle;
- quantity + unit legend;
- min/max/reference labels;
- vector-scale legend;
- time indicator;
- parameter summary;
- solver/provenance badge for analysis mode;
- selected feature label;
- conservation/error diagnostic badge.

Presentation policies should support density levels:

```text
none
minimal
important_only
analysis
teaching
```

Scientific values should come from semantic objects/metrics, not be re-derived by renderer code.

## Axes and spatial reference

Axes should be explicit presentation objects rather than permanent decoration on every Scene.

Axes policy may specify:

- world/scientific coordinate frame;
- axis names;
- units;
- tick density;
- grid-plane visibility;
- origin marker;
- scale bar;
- equal/aspect-correct presentation.

For relativity, manifolds, projections, or other nontrivial coordinates, the domain/view must explicitly define what the displayed axes mean. The presentation system must not pretend projected coordinates are the original higher-dimensional coordinates.

## Lighting policy

Lighting should improve shape readability without encoding scientific values accidentally.

Renderer-neutral lighting intents may include:

- `flat_analysis`;
- `scientific_studio`;
- `soft_volume_context`;
- `rim_emphasis`;
- `unlit_data` for data whose colors must remain photometrically stable.

Scientific color maps should be protected from arbitrary lighting distortion where the selected policy requires quantitative color reading.

## Animation grammar

Spectra already owns engine time. Presentation animation is a second, composable layer over scientific time.

Distinguish:

```text
scientific time
    simulation state changes

presentation time
    reveal, camera, labels, emphasis, explanation pacing
```

The system must not silently retime scientific data in a way that changes physical interpretation.

Recommended animation operations:

- fade;
- draw/reveal path;
- stagger groups;
- camera move;
- label reveal;
- legend reveal;
- highlight/focus;
- compare transition;
- scientific-time playback;
- pause/hold at meaningful states.

A premium explanatory sequence may be:

```text
1. establish geometry
2. reveal source/boundary conditions
3. reveal field representation
4. reveal legend/units
5. begin scientific evolution
6. pause at diagnostic event
7. move camera or highlight region
8. continue evolution
```

## Quality policy

Presentation quality must remain separate from scientific accuracy.

A quality policy may control renderer-facing cost such as:

- glyph density for visual display only;
- surface display subdivision that does not alter solver data;
- antialiasing intent;
- shadow quality;
- post-processing allowance;
- label density;
- animation sampling/render output cadence.

It must never silently reduce solver grid resolution or numerical precision.

If a lower-resolution scientific result is desired, that is an experiment/solver/input decision, not a presentation decision.

## Data reduction for visualization

Large numerical fields often need display decimation.

Rules:

1. preserve the source semantic field/solution unchanged;
2. derive a display sampling specification explicitly;
3. record display sampling separately from solver resolution;
4. use deterministic sampling when reproducibility matters;
5. never claim display sample count is simulation resolution.

Example:

```text
CFD solution: 256^3 numerical cells
presentation VectorGlyphSet: 20 x 20 x 12 sampled arrows
```

The field remains high-resolution even when the display is sparse.

## Backend capability negotiation

Not every renderer supports every premium effect.

A future presentation/backend negotiation layer may advertise capabilities such as:

```text
supports_volumetrics
supports_per_instance_color
supports_screen_space_labels
supports_post_processing
supports_transparency
supports_instanced_glyphs
supports_camera_depth_of_field
```

Presentation policy then selects a deterministic fallback rather than embedding `if blender` inside scientific domains.

## Blender interpretation

Blender should be the first premium reference backend, not the definition of the presentation model.

Potential Blender interpretations include:

- Spectra Material -> Principled/node material;
- presentation background -> World settings;
- scientific studio lighting -> area/key/fill/rim light rig;
- high-cardinality scalar color -> color attribute + shader mapping;
- dense vector/particle display -> batched Curve/Mesh/Geometry Nodes where appropriate;
- label policy -> text objects or screen-space implementation;
- cinematic policy -> camera rig + renderer/compositor configuration.

None of these native details belong in physics, chemistry, PDE, or generic visualization semantics.

## Stable IDs and incremental presentation

Presentation enrichment should preserve base scientific primitive IDs whenever it is styling or animating existing content.

Added presentation primitives should use deterministic namespaces, for example conceptually:

```text
presentation.camera.primary
presentation.legend.temperature
presentation.axes.world
presentation.annotation.time
presentation.light.key
```

This supports incremental Blender/WebGPU updates and avoids rebuilding scientific geometry merely because a presentation preset changed.

## Accessibility

Premium must not mean less readable.

Policies should account for:

- color-vision-safe palettes;
- sufficient text/background contrast;
- redundant encoding when color alone is ambiguous;
- readable label size;
- units always visible when quantitative interpretation matters;
- motion that can be reduced/disabled in interactive clients.

## Determinism and provenance

For `analysis` and `publication`, presentation choices should be deterministic given:

```text
base Scene
presentation preset
explicit overrides
backend capability profile
```

A future saved project/export may record presentation-policy identifiers separately from scientific environment provenance.

Scientific reproducibility and presentation reproducibility are related but distinct.

## What premium presentation must not become

Do not:

- put Blender shader/node logic in scientific domains;
- make every domain implement its own camera/light system;
- let renderer aesthetics alter numerical data;
- encode scientific meaning only through effects unsupported by other backends;
- create thousands of native objects when one batched primitive is enough;
- hide units in decorative labels generated from guessed strings;
- confuse display decimation with solver resolution;
- make AI output the authoritative scientific state.

## Implementation phases after the current numerical milestone is green

### Phase 1 — presentation semantics

Introduce immutable renderer-neutral policy types and a presentation composer around existing `spectra.presentation` helpers.

### Phase 2 — generic scientific framing

Add bounds-driven camera, axes, units, legends, and basic themes.

### Phase 3 — color scales

Add quantity-aware scalar/categorical/cyclic color policies and generic legends.

### Phase 4 — Blender premium mapping

Implement high-quality Blender material/light/camera interpretations while preserving plain-Python import boundaries.

### Phase 5 — explanatory animation grammar

Compose scientific time with reveal/highlight/camera presentation timelines.

### Phase 6 — backend capability negotiation

Allow WebGPU/other backends to interpret the same presentation request with deterministic fallbacks.

## Success criterion

A domain author should be able to produce a correct base Scene without knowing any premium-render details.

A product/user should then be able to request conceptually:

```text
show this Maxwell solution
preset = cinematic
annotations = important_only
camera = orbit_reveal
```

and receive a polished renderer-neutral presentation Scene that Blender can realize at high quality.
