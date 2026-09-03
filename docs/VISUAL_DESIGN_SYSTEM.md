# Spectra Science — Scientific Visual Design System

This document defines the visual-design language that presentation presets should use without moving scientific meaning into a renderer.

The goal is not to force every scene to look identical. The goal is to make independently developed domains look like parts of one serious scientific product.

## Design principles

1. Scientific meaning wins over decoration.
2. Units, sign, direction, magnitude, uncertainty, phase, category, and reference values must remain interpretable.
3. A premium scene should be visually calm before it is visually impressive.
4. Dense data should be simplified through deterministic display sampling, not by changing solver resolution.
5. The same presentation intent should have recognizable character in Blender, WebGPU, a report figure, or a future renderer.
6. Styling must not require scientific domains to know renderer APIs.

## Visual hierarchy

Every presentation should separate four visual levels.

### Primary scientific signal

The quantity or geometry the user is meant to understand first.

Examples:

- a displacement field;
- electric field lines;
- a probability-density surface;
- a particle trajectory;
- a CFD vortex structure.

Primary content receives the strongest contrast, clearest silhouette, and most legible color mapping.

### Secondary scientific context

Information needed to interpret the primary signal:

- source geometry;
- boundary conditions;
- reference surface;
- domain bounds;
- initial state;
- comparison baseline.

Secondary context should be visible but visually quieter.

### Quantitative interpretation

- legends;
- units;
- axes;
- scale bars;
- time;
- parameter values;
- diagnostics.

These should never compete with the primary signal, but publication/analysis modes must keep them explicit.

### Presentation framing

- background;
- decorative lighting;
- camera motion;
- separators;
- subtle grid/background structures.

This layer must never carry unique scientific meaning.

## Typography hierarchy

Renderer-neutral semantic text roles should be used instead of font-specific choices:

```text
title
subtitle
quantity_label
axis_label
tick_label
annotation_primary
annotation_secondary
legend_label
provenance_label
warning_label
```

The backend maps these roles to native typography.

Rules:

- mathematical symbols and units must not be converted to decorative substitutes;
- avoid excessive all-caps for scientific labels;
- use tabular/monospaced numerals only where numerical alignment benefits interpretation;
- title hierarchy may be reduced or removed in analysis mode;
- text size should be specified as semantic scale, not Blender object dimensions.

## Spacing system

Presentation resources should use a small normalized spacing scale rather than arbitrary per-domain offsets:

```text
xs
sm
md
lg
xl
```

Examples:

- legend padding;
- title-to-plot distance;
- annotation offset;
- multi-panel gutter;
- scale-bar spacing.

A backend converts these into world-space or screen-space values according to the scene/camera.

## Color semantics

Color families are selected by data meaning.

### Sequential

For ordered non-negative or monotonic quantities:

- probability density;
- temperature magnitude;
- concentration;
- speed.

### Diverging

For signed quantities with an explicit meaningful center:

- electric potential around zero;
- pressure deviation from a reference;
- signed displacement component;
- residual/error with positive and negative sign.

The center must be explicit. A renderer must not assume zero is meaningful merely because values have both signs.

### Cyclic

For periodic variables:

- phase;
- angle;
- orientation modulo a period.

The endpoints of the palette must communicate continuity.

### Categorical

For distinct non-ordered groups:

- materials;
- species;
- solver implementations;
- experimental categories.

### Confidence/uncertainty

Uncertainty should preferably be encoded through a second channel such as opacity bounds, envelopes, error bars, or surface bands rather than silently distorting the primary quantitative color scale.

## Color-scale policy

A quantitative color scale should be defined by:

```text
quantity_name
unit
scale_type
range_mode
range_min/range_max
center
clamp_mode
missing_value_mode
palette_id
legend_visibility
```

Recommended range modes:

- `data_minmax`;
- `symmetric_about_center`;
- `explicit`;
- `percentile_clip` for display only;
- `shared_comparison_range`.

Percentile clipping is a presentation decision and must be recorded separately from the source data.

## Geometry language

### Lines

Use lines for trajectories, field lines, contours, reference curves, geodesics, and graph-like relationships.

Thickness may encode emphasis or a scientifically defined quantity only when explicitly declared.

### Surfaces

Use surfaces for scalar fields, manifolds, solid geometry, slices, and deformed bodies.

Avoid fake displacement solely for decoration when it could be confused with physical deformation.

### Glyphs

Use glyphs for direction/orientation/vector magnitude.

Rules:

- direction must remain visually unambiguous;
- magnitude scaling must have a declared policy;
- dense fields should be sampled deterministically;
- arrows should stay batched in renderer implementations.

### Point clouds

Use for particles, samples, experimental data, mesh nodes, or dense states.

Size/color encoding should be explicit.

## Material language

Presentation materials should be grouped by intent rather than renderer node recipes:

```text
data_unlit
scientific_matte
context_translucent
surface_quantitative
emissive_emphasis
reference_wire
annotation
```

`data_unlit` is useful when quantitative colors should not be altered by lighting.

`context_translucent` should be used cautiously so occlusion does not destroy interpretation.

## Lighting language

Renderer-neutral rigs:

### `flat_analysis`

Minimal lighting variation. Good for quantitative surfaces and technical inspection.

### `scientific_studio`

Soft key/fill/rim style that reveals three-dimensional form while preserving data color.

### `rim_emphasis`

Useful for dark cinematic scenes where geometry silhouette needs separation.

### `unlit_data`

Presentation geometry carries quantitative color independent of lighting; contextual geometry may still be lit.

Lighting must never imply a scalar gradient that does not exist in the data.

## Camera composition

Recommended composition rules:

- frame the semantic primary subject, not simply all native renderer objects;
- keep legends/annotations outside important silhouettes where possible;
- maintain deterministic framing in publication mode;
- avoid extreme perspective for quantitative geometric comparison;
- use orthographic views where spatial scale comparison matters;
- use perspective/orbit for structural comprehension and cinematic presentation;
- never pick an axis as scientifically privileged without semantic/view guidance.

## Multi-panel comparisons

Comparison views should support consistent:

- camera;
- color range;
- axis scale;
- time;
- legend placement;
- typography hierarchy.

Examples:

```text
reference vs native solver
initial vs final state
parameter A vs parameter B
E field vs B field
probability density vs phase
```

A shared scale should be explicit; auto-ranging each panel independently can produce misleading comparisons.

## Animation character

Premium motion should communicate structure rather than constantly move everything.

Recommended pacing grammar:

```text
establish
reveal
explain
simulate
pause
emphasize
compare
resolve
```

Scientific-time playback and presentation motion must remain separable.

Avoid:

- perpetual camera orbit during quantitative inspection;
- unnecessary bounce/easing on scientific geometry;
- time remapping that changes perceived physical rates without explicit labeling;
- excessive glow or motion blur that hides vector/trajectory structure.

## Preset character

### Analysis

Dense information, neutral styling, explicit units, fast rendering.

### Publication

Minimal, deterministic, high-contrast, exact labels and shared ranges.

### Presentation

Large hierarchy, staged explanation, moderate motion.

### Cinematic

Controlled depth, lower annotation density, intentional camera movement, premium lighting.

### Dark Lab

Dark technical environment, bounded luminous accents, clear readable labels.

The same scientific scene should remain recognizably the same result under all presets.

## Accessibility

Required design constraints:

- color must not be the only channel for critical categorical distinction;
- quantitative palettes should be perceptually ordered when magnitude is ordered;
- labels must maintain contrast against scene background;
- motion-reduced variants should be possible;
- important units and signs must remain visible in analysis/publication modes;
- legends should not depend on tiny gradients that disappear in screenshots/video compression.

## Premium-quality anti-patterns

Do not equate premium with:

- bloom everywhere;
- excessive transparency;
- neon for every quantity;
- tiny floating labels;
- dramatic depth of field that hides scientific content;
- different unrelated color language in every module;
- cinematic camera choices in technical comparison figures;
- renderer-specific style parameters embedded in scientific semantic types.

## Implementation boundary

This document describes presentation policy, not current runtime functionality.

Runtime implementation should follow:

```text
PREMIUM_PRESENTATION_SYSTEM.md
    -> presentation semantic contracts
    -> presentation composer
    -> backend interpretation
```

Blender-specific mappings belong in `BLENDER_PREMIUM_PRESENTATION.md`.

## Success criterion

A Maxwell animation, thermoelastic solid, quantum wavefunction, CFD flow, and experiment Pareto plot should look like five views from the same scientific product while retaining the visual grammar appropriate to each kind of data.
