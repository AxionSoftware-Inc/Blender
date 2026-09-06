# Spectra Science — Quantum Probability + Phase Flagship Validation Handoff

Status: **flagship #3 implemented on top of the pending Maxwell + Electrostatic showcase stack; validation pending**.

Last fully verified baseline:

```text
183b8aa869f1643462fbfb00193e109d65c323e7
```

That baseline reported 300 passing tests, 119 domains / 468 providers, real compiled native RK4, and Blender 5.2 quantitative/native smoke PASS.

Do not promote the current combined head until the earlier stacked showcase handoffs and this handoff pass together.

## Purpose

This flagship proves that a real complex-valued Schrodinger solve can feed two scientifically distinct presentation channels without confusing physical data with display geometry:

```text
free 2D electron wavepacket in SI meters
    -> existing physics.quantum.schrodinger2d.solve
    -> normalized complex psi(x,y,t)
    -> final-state probability density |psi|^2 [m^-2]
    -> final-state phase arg(psi) [rad]
    -> two renderer-neutral Surface panels
    -> VIRIDIS probability + PHASE cyclic phase
    -> quantitative presentation
    -> QuantitativeBlenderBackend
```

No Schrodinger integrator or Laplacian is implemented in `spectra.showcases`.

## New public showcase API

```text
spectra.showcases.QuantumWavepacketShowcaseConfig
spectra.showcases.solve_quantum_wavepacket_showcase
spectra.showcases.build_quantum_wavepacket_base_scene
spectra.showcases.build_quantum_wavepacket_scene
spectra.showcases.PROBABILITY_DENSITY_2D
spectra.showcases.RADIAN
```

## Canonical scientific model

Default model:

```text
free 2D packet
mass: electron-mass reference
x domain: +/- 6 nm
y domain: +/- 4 nm
initial center x: -2 nm
Gaussian sigma: 0.8 nm
carrier wave number: 3e9 1/m
end time: 6 fs
fixed boundaries
```

The solver grid remains SI meters and the Schrodinger equation uses the existing typed mass semantics and reduced Planck constant.

## Scientific coordinates vs display coordinates

Nanometer scientific coordinates are too small for ordinary renderer camera clipping/framing. The showcase therefore uses explicit display mapping:

```text
1 display unit = 1 nm
```

by default.

This affects only Scene geometry. The numerical grid, wave number, mass, time, and probability calculation remain SI.

Likewise, the probability panel height is normalized to a configurable display height. The scalar vertex attribute still carries the physical numeric probability density.

Never claim that the Surface z coordinate is raw probability density.

## Probability-density semantics

Probability Surface carries:

```text
name        = probability_density
association = vertex
kind        = scalar
quantity_id = probability_density
unit        = m^-2
```

Presentation uses:

```text
palette    = VIRIDIS
range mode = DATA
```

The source scalar values must remain unchanged by color mapping.

## Phase semantics

Phase Surface carries:

```text
name        = phase
association = vertex
kind        = scalar
quantity_id = wavefunction_phase
unit        = rad
range       = [-pi, +pi]
```

Phase is mapped with the cyclic `PHASE` palette, not a sequential/diverging palette.

Where probability density is very small, phase is physically/numerically uninformative. The showcase therefore fades phase alpha as density approaches a configured fraction of peak probability. This is an explicit presentation confidence cue, not a modification of the stored phase scalar.

The generic presentation composer currently has one primary legend/color-scale context, so the automatic legend is for probability density. The phase panel has an explicit text label documenting cyclic `-pi...pi rad` semantics.

## Deliberate static final-state choice

This first quantum flagship solves a time-dependent Schrodinger problem but presents the **final scientific snapshot** as a static comparison scene.

Reasons:

- probability and phase require two distinct color policies;
- current Scene-v5 quantitative color attributes are static per snapshot;
- dynamic per-frame color-attribute animation is not yet a generic Timeline contract;
- static final-state validation cleanly proves solver -> semantic data -> premium quantitative Blender realization.

A later animated quantum milestone should add dynamic attribute semantics rather than smuggling phase/color updates into renderer-specific code.

## Required validation sequence

### G0 — repository

```text
git status
git pull
```

Record starting SHA. Do not create GitHub Actions.

### G1 — compile/import boundary

```text
python -m compileall spectra
```

PASS required.

Outside Blender import:

```text
spectra.showcases
spectra.showcases.quantum_wavepacket
```

No eager `bpy` import.

### G2 — targeted plain-Python tests

Run at minimum:

```text
tests/test_quantum_wavepacket_showcase.py
tests/test_wave_equation_schrodinger2d.py
tests/test_schrodinger_domain.py
tests/test_spatial_quantum_domain.py
tests/test_quantitative_presentation.py
tests/test_quantitative_shared_scale_and_legend.py
```

Also run Maxwell and Electrostatic targeted sets when validating the combined head.

Root-cause fixes only.

### G3 — numerical/scientific invariants

For the small validation config confirm:

- the initial state is normalized by the existing Schrodinger domain;
- initial probability mass is approximately 1;
- final probability mass remains acceptably close to 1 for the configured reference integration;
- the positive carrier wave number produces increasing expectation value `<x>` over the short free evolution;
- solver duration equals configured SI end time;
- no showcase-specific Schrodinger RHS/Laplacian exists;
- high-level solve still dispatches through the existing complex PDE / stable ODE numerical role.

Do not hardcode the exact ODE implementation in the showcase test unless a solver-policy test explicitly asks for it.

### G4 — probability/phase data invariants

Confirm:

- two Surface panels exist;
- probability scalar is non-negative and nonzero;
- probability unit is `m^-2`;
- phase values remain within `[-pi, pi]`;
- phase unit is `rad`;
- probability and phase have distinct display-color attributes;
- probability Surface height max equals configured display height, proving display normalization;
- raw probability values are not replaced by normalized heights;
- low-density phase colors contain low alpha;
- high-density phase colors remain visible;
- phase scalar values themselves are not alpha-masked or rewritten.

### G5 — presentation invariants

Confirm:

- automatic quantitative legend is for `probability_density [m^-2]`;
- probability palette is VIRIDIS;
- phase palette is cyclic PHASE with fixed `[-pi, pi]` input range;
- camera/axes/title resources are deterministic presentation resources;
- title is `Quantum Wavepacket · Probability + Phase`;
- Scene is static because this milestone presents the final scientific snapshot;
- display labels explicitly state nm mapping, femtosecond scientific time, and normalized probability height semantics.

### G6 — full pytest

```text
pytest -q
```

PASS required. Record actual count.

### G7 — DomainCatalog

Run normal catalog/provider probe.

The showcase is not a Domain and should not add catalog providers merely by existing. Record actual counts rather than forcing historical numbers.

### G8 — Blender 5.2 quantum smoke

Run:

```text
blender --background --python examples/blender_quantum_wavepacket_smoke.py
```

Required behavior:

- one probability mesh object;
- one phase mesh object;
- native `spectra_display_color` POINT attribute on both;
- native attribute sample count matches Surface vertex count on both;
- one quantitative material per panel;
- phase native alpha contains both low and high values;
- static re-apply preserves probability object/datablock identity;
- static re-apply preserves phase object/datablock identity;
- native color attributes remain after re-apply;
- cleanup removes Spectra-owned collection.

### G9 — stacked Blender regressions

For combined-head promotion rerun:

```text
examples/blender_maxwell_showcase_smoke.py
examples/blender_electrostatic_lab_smoke.py
examples/blender_quantitative_smoke.py
```

plus the older static/wave/EM smoke suite used by the latest verified baseline if practical.

### G10 — source-boundary audit

Confirm:

- no `bpy` import in `spectra/showcases/quantum_wavepacket.py`;
- no new quantum numerical solver exists in showcase code;
- SI grid coordinates remain meters inside the solver;
- display coordinate scaling happens only while creating Scene vertices;
- probability height normalization does not alter the `probability_density` VisualAttribute;
- phase colors use PHASE cyclic mapping;
- low-density fading modifies display alpha only;
- no backend-specific phase computation exists.

## Known deliberate limitations

This milestone does not claim:

- production quantum mechanics fidelity for arbitrary potentials/boundaries;
- Crank-Nicolson/split-operator/spectral production integrators;
- adaptive quantum grids;
- dynamic phase/probability color attributes on a Timeline;
- volume probability rendering;
- Bloch sphere / spin / many-body / quantum chemistry / DFT;
- physical measurement/collapse workflows;
- screen-space dual colorbars.

It is a canonical integration proof for complex scientific state -> physically meaningful derived quantities -> renderer-neutral premium visualization.

## Promotion rule

Current combined development-head promotion requires:

1. Maxwell applicable gates PASS;
2. Electrostatic applicable gates PASS;
3. Quantum applicable gates PASS;
4. full pytest PASS;
5. DomainCatalog probe PASS;
6. targeted Blender smokes PASS;
7. repo clean/synced at recorded SHA.

Final report should include:

```text
Final SHA
repo clean/synced
compileall
full pytest + actual count
initial failures
DomainCatalog domains/providers
prior flagship gate status
quantum initial/final probability mass
initial/final <x>
scientific end time
probability density min/max + unit
phase range + unit
native probability/phase attribute counts
phase alpha range
static identity result
stacked Blender regression result
cleanup result
root fixes
remaining limitations
GitHub Actions absent
```
