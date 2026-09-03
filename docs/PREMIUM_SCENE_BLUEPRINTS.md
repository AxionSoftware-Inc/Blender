# Spectra Science — First Five Premium Scene Blueprints

Status: **design blueprint; presentation runtime not yet implemented**.

This document narrows `SHOWCASE_SCENARIOS.md` into the first five renderer-neutral premium scenes to build after the generic presentation composer and quantitative color policy are implemented.

Each blueprint defines:

- scientific source/result;
- explicit visualization semantics;
- presentation intent;
- deterministic resource IDs;
- quantitative color meaning;
- animation structure;
- Blender acceptance target;
- what must not be renderer-specific.

The same base blueprint should remain meaningful for WebGPU or another backend.

---

# 1. Electrostatic Field Laboratory

## Product purpose

Demonstrate the simplest complete Spectra story:

```text
physical sources
  -> numerical solve
  -> potential field
  -> electric field
  -> field-line/view semantics
  -> premium scene
```

## Scientific input

Recommended canonical setup:

```text
one +q source
one -q source
symmetric placement around origin
3D electrostatic potential domain
```

Use existing typed point-source/deposition/electrostatic capabilities.

## Required views

```text
potential scalar slice
E-field VectorGlyphSet
field-line bundle
source markers
```

Do not calculate field lines inside Blender.

## Presentation preset

Primary:

```text
dark_lab
```

Secondary acceptance:

```text
publication
```

## Quantity/color semantics

Potential slice:

```text
diverging around 0 V when the chosen reference makes zero meaningful
```

Electric-field arrows:

```text
categorical/semantic E-field identity
optional magnitude scale
```

Positive/negative source identity may use distinct categorical colors, but sign must also be clear through labels/symbols where needed.

## Deterministic IDs

Suggested:

```text
science.electrostatic.sources
science.electrostatic.potential_slice
science.electrostatic.e_vectors
science.electrostatic.field_lines

presentation.camera.primary
presentation.legend.potential
presentation.legend.e_field
presentation.annotation.title
presentation.annotation.time
presentation.light.key
presentation.light.fill
presentation.light.rim
```

Actual scientific IDs should preserve existing domain/view IDs if already defined; do not rename them merely to match this document.

## Camera

Default:

```text
perspective_context
```

Frame both sources and most field lines.

Avoid a camera angle that visually overlaps +q and -q.

Publication variant may use a more orthographic view of the scalar slice.

## Animation

Sequence:

```text
1. reveal source charges
2. reveal potential slice
3. reveal field arrows
4. draw field lines
5. show legends/units
6. optional slow camera orbit
```

Scientific field is static; animation is presentation-only.

## Acceptance

- field lines terminate/orient consistently with field semantics;
- potential legend matches displayed scalar mapping;
- no per-field-line Blender object explosion;
- switching dark_lab -> publication does not recompute potential;
- source labels remain readable.

---

# 2. Maxwell Electromagnetic Wave

## Product purpose

Demonstrate time-dependent vector science, stable batched updates, scientific time, and premium animation.

## Scientific input

Use the existing Maxwell/plane-wave reference path with a clean propagating wave.

Recommended canonical representation:

```text
propagation along +x
E perpendicular to B
E and B perpendicular to propagation
```

## Required views

```text
E VectorGlyphSet
B VectorGlyphSet
propagation reference axis/path
optional field-energy annotation
```

## Presentation preset

Primary:

```text
cinematic
```

Secondary:

```text
analysis
```

## Color semantics

E and B are different physical quantities; use stable semantic identity colors rather than one shared scalar colormap.

If magnitude variation is encoded:

```text
size/length or per-instance value channel
```

with explicit vector scale.

Do not imply E and B have the same units or numerical scale.

## Camera

Default:

```text
perspective_context
```

Look diagonally along propagation direction so transverse relationship is clear.

Camera may move slowly, but should not rotate so aggressively that E/B orthogonality becomes hard to perceive.

## Animation

Scientific playback is primary:

```text
E(x,t), B(x,t)
```

Presentation layer only adds:

```text
initial reveal
labels
time indicator
optional slow camera move
```

Never retime E and B independently.

## Blender acceptance

- E and B remain batched `VectorGlyphSet` representations;
- object/datablock identity stable across frames;
- no object-count growth;
- presentation lights/camera do not rebuild vector geometry;
- E/B update remains synchronized at one Spectra time.

---

# 3. Quantum Wavepacket — Probability + Phase

## Product purpose

Demonstrate complex-valued science where one result has multiple valid views and different color semantics.

## Scientific source

Use a Schrödinger solution with visibly evolving wavepacket structure.

Prefer a setup whose numerical behavior is stable enough for a canonical showcase.

## Required views

Two coordinated views:

```text
probability density |ψ|²
phase arg(ψ)
```

Optional third view:

```text
probability current vectors
```

## Presentation preset

Primary:

```text
presentation
```

Secondary:

```text
publication
```

## Color semantics

Probability density:

```text
sequential, non-negative
```

Phase:

```text
cyclic
```

Never render phase with a sequential heat scale.

If probability density is used as surface height and phase as color, legend must make the dual encoding explicit.

## Layout

Recommended first implementation:

```text
side-by-side or vertically separated coordinated panels
```

Do not force both quantities into one ambiguous object if the current Scene model cannot communicate the mapping clearly.

## Camera

For 2D slice/surface presentation:

```text
controlled perspective or orthographic analysis
```

Publication variant should minimize distortion.

## Animation

```text
1. establish axes/domain
2. reveal probability view
3. reveal phase legend/view
4. start scientific evolution
5. pause/highlight one interference/packet event
```

All views sample the same scientific time.

## Acceptance

- probability scale never becomes negative;
- phase legend is cyclic;
- one global time indicator;
- synchronized views;
- switching presentation preset does not change ψ solution;
- view sampling is clearly distinct from solver grid resolution.

---

# 4. Thermoelastic Solid

## Product purpose

Demonstrate real multiphysics composition:

```text
heat source
  -> temperature field
  -> thermal strain
  -> displacement/stress
  -> deformed geometry + quantitative overlays
```

## Scientific source

Use a simple block/plate/grid where heating produces an understandable deformation and stress pattern.

Initial showcase should avoid complicated geometry so the physics remains visually obvious.

## Required views

```text
deformed lattice/PointCloud or surface
source/temperature scalar view
von Mises stress or displacement magnitude
optional undeformed reference wireframe
```

## Presentation preset

Primary:

```text
presentation
```

Secondary:

```text
analysis
```

## Color semantics

Temperature:

```text
sequential
```

Temperature difference from reference, if shown:

```text
diverging only when ΔT sign matters
```

Von Mises stress:

```text
sequential non-negative
```

Signed displacement component:

```text
diverging
```

Do not color one surface simultaneously by temperature and stress without a clear dual-view strategy.

## Deformation scale

Visual deformation amplification may be needed.

If used, it must be explicit:

```text
display deformation scale = N×
```

and shown in annotation/legend.

Never imply amplified visual displacement is the physical displacement magnitude.

## Camera

Perspective that shows 3D deformation while keeping boundary/support context visible.

Analysis variant may add axes/reference geometry.

## Animation

```text
1. show undeformed solid and boundary/support context
2. reveal heat source
3. reveal temperature field
4. begin thermal evolution
5. progressively reveal/deform structure
6. show stress/displacement diagnostic
```

Scientific temperature and displacement times must remain synchronized if coupled history is shown.

## Blender acceptance

- deformed PointCloud/surface updates in place when topology unchanged;
- quantitative colors remain stable across frames unless policy explicitly changes;
- no scientific recompute for camera/theme changes;
- deformation-scale annotation accurate;
- owned presentation resources clean up correctly.

---

# 5. Schwarzschild Geodesics

## Product purpose

Demonstrate geometry/relativity, explicit projection semantics, clean curves, and cinematic presentation without pretending renderer space is spacetime itself.

## Scientific source

Use Schwarzschild metric/geodesic foundation with a carefully chosen set of trajectories whose qualitative behavior is understandable.

The showcase should be described as a geodesic visualization/projection, not a full black-hole astrophysical ray-tracing simulation unless that capability exists later.

## Required views

```text
central reference/body/horizon representation
multiple geodesic Polylines
initial condition/source markers
coordinate/projection annotation
```

## Presentation preset

Primary:

```text
cinematic
```

Secondary:

```text
publication
```

## Color semantics

Different geodesics:

```text
categorical or parameter-encoded palette
```

If color encodes conserved quantity/initial parameter, legend must say exactly which parameter.

Do not use decorative gradient as if it were gravitational potential unless that field is explicitly computed/shown.

## Camera

Cinematic version:

```text
perspective_context with slow orbit
```

Publication:

```text
projection-aligned deterministic camera
```

The view must identify what spatial projection/coordinates are shown.

## Animation

Two valid modes:

### Path reveal

Presentation-only draw of already computed geodesic curves.

### Particle traversal

A marker moves along the computed geodesic parameterization.

Do not reinterpret animation time as physical coordinate/proper time unless the chosen trajectory semantics explicitly define that mapping.

## Acceptance

- no renderer-side geodesic integration;
- projection/coordinate meaning visible;
- central geometry is not falsely presented as a physically rendered event horizon if semantics are only a reference surface;
- curve reveal preserves geodesic points;
- camera movement does not change scientific trajectory data.

---

# Cross-scene presentation rules

All five scenes must obey:

```text
scientific result immutable
presentation deterministic
scientific IDs stable
presentation IDs namespaced
units visible for quantitative scales
scientific time separate from presentation time
no backend-specific science
no display decimation confused with solver resolution
```

## Required preset matrix

Each scene should eventually be checked in at least two presets:

| Scene | Primary | Secondary |
| --- | --- | --- |
| Electrostatic Lab | dark_lab | publication |
| Maxwell Wave | cinematic | analysis |
| Quantum Wavepacket | presentation | publication |
| Thermoelastic Solid | presentation | analysis |
| Schwarzschild Geodesics | cinematic | publication |

This proves presets are cross-domain rather than one-off scene templates.

# Phase ordering

Do not implement all five immediately.

Recommended runtime sequence:

```text
1. Maxwell
   proves animated vector + camera/title/reveal

2. Electrostatic
   proves quantitative diverging scalar legend + field composition

3. Quantum
   proves multiple coordinated views + cyclic color

4. Thermoelastic
   proves deformation + quantitative multiphysics overlays

5. Schwarzschild
   proves explicit projection semantics + premium curve presentation
```

# Output targets

Each blueprint should ultimately support:

```text
interactive Blender scene
still image
video/animation
renderer-neutral Scene inspection
future WebGPU preview
```

Publication variants should eventually support reproducible color/camera metadata in export sidecars.

# Success criterion

When these five scenes work through one presentation system, Spectra can credibly demonstrate that premium scientific presentation is a reusable platform layer rather than custom Blender artistry written separately for each subject.