# Spectra Science — Maxwell Flagship Validation Handoff

Status: **post-`183b8aa...` Maxwell showcase batch; validation pending**.

Last fully verified baseline:

```text
183b8aa869f1643462fbfb00193e109d65c323e7
```

That baseline reported 300 passing tests, 119 domains / 468 providers, real compiled native RK4, and Blender 5.2 quantitative/native smoke PASS.

Do not promote the Maxwell batch until the gates below pass.

## Purpose

This is the first of five canonical premium scientific showcases. It must prove reuse of the existing platform rather than introduce another scientific subsystem.

Pipeline under test:

```text
PlaneElectromagneticWave (SI semantics)
    -> TimeVectorFieldAnimation3D
    -> batched E/B VectorGlyphSet + field-profile traces
    -> generic Scene + scientific Timeline
    -> PresentationIntent
    -> presented Scene
    -> Blender transport/backend
```

No Maxwell/EM solver is duplicated in the showcase package.

## New showcase API

```text
spectra.showcases.MaxwellWaveShowcaseConfig
spectra.showcases.build_maxwell_wave_base_scene
spectra.showcases.build_maxwell_wave_scene
```

Canonical defaults:

```text
propagation: +x
E polarization: +y
B direction: +z
wavelength: 4 m
E amplitude: 1 N/C
visible span: 3 wavelengths
scientific evolution: 2 periods
spatial samples: 49
temporal samples: 121
recommended Blender playback: 4 s
```

The wave uses the physical default speed of light. The scientific Timeline therefore remains nanosecond-scale SI time.

## Display scaling

Scientific field units remain:

```text
E -> N/C
B -> T
```

For joint visual readability:

```text
E_display = E / E0
B_display = c * B / E0
```

so E and B have comparable visual arrow amplitudes. This is presentation scaling only. The label explicitly states that B is displayed as `c·B`.

Do not rewrite scientific B values or claim E and B have the same units.

## Scientific time vs playback time

This batch extends the Blender transport boundary with optional:

```text
playback_duration
```

`Scene.timeline.duration` remains scientific time.

For the canonical showcase:

```text
~tens of ns scientific time -> 4 s Blender playback
```

The frame transport maps proportionally into the exact scientific interval.

Backward compatibility requirement:

```text
playback_duration=None
```

must preserve the previous `1 Blender second = 1 scientific second` behavior.

### Important presentation rule

The canonical Maxwell scene deliberately disables staggered presentation reveal.

Reason: the current Scene owns one Timeline. Adding a seconds-long reveal to a nanosecond scientific Timeline would change the Timeline duration and corrupt the meaning of scientific time.

Until a true independent presentation-timeline model exists, do not add seconds-long presentation tracks to this SI Maxwell Scene.

## Scene composition fix

`namespace_scene()` now preserves `Track.owner` while rewriting target IDs.

Validate that namespacing never converts a `presentation` track back to the default `scientific` owner.

## Required validation sequence

### G0 — repository

```text
git status
git pull
```

Record starting SHA. Do not create GitHub Actions.

### G1 — compile/import

```text
python -m compileall spectra
```

PASS required.

Import outside Blender:

```text
spectra.showcases
spectra.showcases.maxwell_wave
spectra.backends.blender.timeline
```

No eager `bpy` import.

### G2 — targeted plain-Python tests

Run at minimum:

```text
tests/test_maxwell_showcase.py
tests/test_blender_timeline_controller.py
tests/test_scene_composition.py
tests/test_em_plane_wave.py
tests/test_presentation.py
tests/test_presentation_recomposition.py
```

Root-cause fixes only.

### G3 — Maxwell structural/scientific invariants

Confirm:

- canonical propagation is +x;
- E is +y at zero phase;
- B is +z at zero phase;
- physical `B0 = E0/c` relation remains true;
- E/B display amplitudes are intentionally equal only after display scaling;
- E and B each compile to one `VectorGlyphSet`;
- spatial instance count remains 49 by default;
- electric and magnetic trace polylines exist;
- E/B vector and trace tracks are owner `scientific`;
- `Scene.timeline.duration == 2 * wavelength / c` for the default two-period config;
- sampling changes vector/trace values while topology/IDs stay stable;
- presented Scene does not add a seconds-long reveal track;
- presented Scene retains the scientific duration exactly;
- title/subtitle/camera are presentation resources.

### G4 — playback scaling

Validate the mapping independently of Blender:

```text
20 ns science over 4 s playback
frame 1   -> 0 ns
frame 61  -> 10 ns
frame 121 -> 20 ns
```

At 30 fps with start frame 1.

Also validate legacy mapping with `playback_duration=None`.

### G5 — full pytest

```text
pytest -q
```

PASS required. Record actual test count; do not reuse 300.

### G6 — DomainCatalog

Run normal catalog/provider probe.

Expected architecture property: the showcase package is not a Domain and should not change catalog ownership merely by existing.

Record actual counts. If they differ from 119 / 468, explain the real reason rather than forcing counts.

### G7 — Blender 5.2 flagship smoke

Run:

```text
examples/blender_maxwell_showcase_smoke.py
```

Required behavior:

- scientific Timeline remains nanosecond-scale;
- Blender transport spans 4 seconds / frames 1..121 at 30 fps;
- E `VectorGlyphSet` is one native batched representation;
- B `VectorGlyphSet` is one native batched representation;
- each default E/B batch contains 49 vector splines in the current Curve backend;
- electric/magnetic trace objects exist;
- start/intermediate/end seeks update in place;
- E/B object identity remains stable;
- E/B datablock identity remains stable;
- trace object/datablock identity remains stable;
- no object-count explosion;
- controller close cleans the owned collection.

### G8 — existing Blender EM regression

Rerun:

```text
examples/blender_em_wave_animation.py
```

and any existing targeted E/B identity/leak smoke used by the local validation setup.

The old normalized-speed example must continue working because `playback_duration` is optional.

### G9 — source-boundary audit

Confirm:

- no new Maxwell solver was created in `spectra/showcases`;
- no `bpy` entered scientific/showcase construction modules;
- no renderer SDK entered Core/domain semantics;
- no scientific unit was rewritten for visual convenience;
- no dense E/B field expanded into one Blender object per vector;
- `Track.owner` remains preserved through Scene namespace composition.

## Known deliberate limitations

This milestone does not attempt to solve:

- Geometry Nodes VectorGlyphSet rendering;
- high-cardinality per-vector native color attributes for VGS;
- independent presentation Timeline / intro-hold-outro sequencing;
- dynamic frame-by-frame scientific time label;
- production Maxwell FDTD/PML/dispersive materials;
- video rendering/export automation.

Those are not blockers for this first canonical integration scene.

## Promotion rule

Only after applicable gates pass should this bounded Maxwell batch become the next verified checkpoint.

Final report should include:

```text
Final SHA
repo clean/synced
compileall
full pytest + actual count
initial failures
DomainCatalog domains/providers
Maxwell targeted tests
scientific duration / period
playback mapping
E/B physical relation
E/B instance/native object counts
Blender start/mid/end identity
cleanup result
existing EM regression result
root fixes
remaining limitations
GitHub Actions absent
```
