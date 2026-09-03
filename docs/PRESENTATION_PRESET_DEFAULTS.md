# Spectra Science — Initial Presentation Preset Defaults

Status: **design defaults for Phase 1/2; not implemented runtime**.

This document freezes a conservative first set of renderer-neutral presentation defaults for `analysis`, `publication`, `presentation`, `cinematic`, and `dark_lab`.

The purpose is not to define artistic taste forever. It gives the first runtime implementation deterministic defaults that can later evolve through explicit versioned presentation policy changes.

## Global rules

All presets obey:

- scientific geometry/data remains authoritative;
- presentation never changes solver resolution;
- quantitative colors are not recolored decoratively;
- Scene-local bounds drive framing;
- explicit user overrides win over preset defaults;
- unsupported preferred features degrade deterministically;
- unsupported required scientific representation fails explicitly;
- renderer-specific settings remain backend-private.

## Common baseline

Unless overridden:

```text
camera padding = 0.12
annotations title = none
subtitle = none
show_time = true when Scene duration > 0
show_provenance = false
legend show_units = true
legend show_min_max = true
quality level = interactive
scientific playback = true
presentation-owned IDs deterministic
```

## analysis

Intent: quantitative inspection and engineering/scientific work.

```text
camera mode:
  orthographic_analysis when a stable planar/2D view is explicitly known
  otherwise fit_all

camera projection:
  orthographic for explicit planar analytical views
  perspective only when 3D depth is semantically useful

lighting:
  flat_analysis

axes:
  visible = true when coordinate semantics are known
  grid = false by default
  equal_scale = true for spatial geometry where meaningful

annotations:
  density = analysis
  title optional
  time visible for animated results
  provenance hidden by default

legend:
  visible for explicitly quantitative color binding
  compact = false
  units = true
  min/max = true

animation:
  reveal = none
  camera_motion = false

materials:
  quantitative data prefers unlit/low-distortion treatment
  context geometry restrained

post-processing:
  disabled/preferred false
```

The analysis preset must remain readable without shadows, glow, DOF, bloom, or cinematic effects.

## publication

Intent: reproducible figure/paper/report output.

```text
camera mode = deterministic fit_all or explicitly supplied orthographic view
lighting = unlit_data or restrained flat lighting
axes = visible only when they improve scientific interpretation
annotations = minimal
legend = visible for quantitative maps
legend compact = true when layout pressure requires it
animation reveal = none
camera motion = false
post-processing = disabled
quality = high/final at export layer, not solver layer
```

Additional rules:

- no decorative camera angle that distorts quantitative comparison;
- avoid perspective for plots/flat slices unless explicitly desired;
- deterministic shared color ranges for comparison panels;
- no vignette/DOF/motion blur by default;
- transparent or light background may be requested by export/backend policy, not encoded by scientific domains.

## presentation

Intent: lecture/demo/business/scientific storytelling while preserving clarity.

```text
camera mode = fit_primary when context identifies a primary object, otherwise fit_all
projection = perspective for 3D scenes, orthographic for explicit 2D views
lighting = scientific_studio
axes = context-dependent; visible for analytical plots, optional for spatial demos
annotations = teaching
legend = visible for quantitative data
animation reveal = staggered
reveal duration = 0.6 s
stagger = 0.12 s
camera motion = false initially
quality = interactive/preview
```

Presentation preset may stage content, but must not delay/re-time scientific state evolution in a way that changes its meaning. Presentation and scientific timelines remain separately owned even when merged for playback.

## cinematic

Intent: premium authored-looking scientific visualization.

Initial conservative defaults:

```text
camera mode = perspective_context
lighting = scientific_studio
optional rim emphasis = preferred
annotations = important_only
axes = hidden unless needed for meaning
legend = visible when data color is quantitative
animation reveal = staggered/staged
camera motion = preferred only after generic camera-track support is implemented safely
quality = preview/high
post-processing = preferred, never required for scientific interpretation
```

Rules:

- cinematic treatment may alter context lighting/material style;
- quantitative data colors remain tied to the same scale/legend;
- no scientific value may be represented only through bloom/glare;
- camera motion must not cause unreadable labels/legends;
- default perspective FOV remains restrained rather than extreme wide-angle.

## dark_lab

Intent: premium dark scientific workspace/demo aesthetic.

```text
theme = dark_lab
camera mode = perspective_context for 3D, explicit analysis camera for 2D
lighting = rim_emphasis/scientific_studio
annotations = important_only
axes = minimal
legend = visible when quantitative
animation = modest staged reveal
quality = interactive/preview
```

Current Scene v4 limitation:

- no generic background/world resource exists.

Therefore Phase 1 `dark_lab` may change only expressible presentation resources such as labels/material roles/lights. A true dark world/background remains a later backend/environment capability checkpoint.

## Color defaults by quantity semantics

Preset does not override semantic scale class.

Default semantic choices:

```text
non-negative magnitude/density -> sequential
signed quantity around meaningful zero/reference -> diverging
phase/angle -> cyclic
categories/states -> categorical
```

Range defaults:

```text
analysis -> data range unless explicit scientific reference requires otherwise
publication -> explicit/shared range preferred for comparisons
presentation -> data or explicit shared range
cinematic -> same scientific range as analytical representation; aesthetics do not change range meaning
dark_lab -> same as corresponding scientific view
```

## Default camera constants

Initial generic values, subject to implementation validation:

```text
perspective fov_y = 50 degrees
camera padding = 12%
minimum framing radius epsilon = small positive engine constant
near clip = derived, always positive
far clip = derived from target radius/distance with safety margin
```

The camera helper should calculate in Scene-local space and use `Transform3D.look_at()`.

## Default lighting roles

### flat_analysis

Prefer minimal generic light burden. Quantitative unlit data should not depend on lighting.

### scientific_studio

Conceptual roles:

```text
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Initial implementation may start with key + fill if rim is unnecessary.

Relative intensity should be deterministic and backend-neutral; generic `Light.intensity` is not claimed to be a physical photometric unit.

### rim_emphasis

Adds/rebalances presentation light for silhouette separation. Must not affect scientific values.

### unlit_data

Quantitative data material remains independent of scene lighting where possible. Context geometry may still use lights.

## Annotation defaults

### analysis

May show:

- time;
- units;
- primary quantity;
- key diagnostics when explicitly supplied.

### publication

Minimal title/legend/ticks only.

### presentation

Teaching labels and important parameters allowed.

### cinematic/dark_lab

Keep on-screen clutter low; scientific units/legend still mandatory when required for interpretation.

## Reveal defaults

Only presentation/premium presets request reveal by default.

```text
presentation: staggered, 0.6 s duration, 0.12 s spacing
cinematic: staged/staggered, same initial values until richer grammar lands
dark_lab: modest staggered
analysis/publication: none
```

Reveal must obey `ANIMATION_COMPOSITION_CONTRACT.md`:

- do not duplicate an existing `(target_id, property_path)` track;
- scientific ownership wins;
- presentation-owned targets are unrestricted by scientific tracks.

## Quality defaults

Quality is display/render intent, not numerical precision.

```text
analysis = interactive
publication = high/final when exported
presentation = interactive/preview
cinematic = preview/high
dark_lab = interactive/preview
```

Display glyph limits/LOD remain explicit policy and must never change solver/grid resolution.

## Required vs preferred features

Examples:

```text
quantitative continuous color = may be REQUIRED
screen-space legend = usually PREFERRED
volumetric effect = PREFERRED
DOF = PREFERRED
post-processing = PREFERRED
exact unit labels = REQUIRED for a unit-bearing quantitative legend
```

Fallback logic must preserve this distinction.

## Initial preset-version stance

Before public stabilization, presets may evolve with the application.

Once persistent project files store preset IDs with expectations, introduce either:

- a presentation policy version; or
- explicit resolved overrides in project presentation variants.

Never silently reinterpret an old project’s scientific color range because a preset aesthetic changed.

## Acceptance

Phase 1 runtime should verify:

- each preset resolves deterministically;
- explicit overrides win;
- all numeric defaults finite;
- Scene-local camera framing;
- no scientific primitive mutation;
- analysis/publication produce no reveal tracks by default;
- presentation/cinematic/dark_lab reveal respects track ownership;
- repeated composition is idempotent.

## Success criterion

A caller can choose a single high-level preset and receive a consistent renderer-neutral starting presentation without scientific domains knowing anything about camera rigs, Blender shaders, compositor effects, or product UI styling.