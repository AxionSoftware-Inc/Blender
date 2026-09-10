# Showcase continuation handoff

This file is the compact continuation note for the current product/showcase development stack.

## Rule

Do **not** treat the current showcase stack as a new green baseline until local validation passes. Keep the previously established Maxwell checkpoint separate. New showcases should compose existing domains/capabilities; do not duplicate solvers inside `spectra/showcases`.

## Current state

### #1 Maxwell

Already implemented as the first flagship showcase. Do not redesign it during the next steps unless validation finds a real regression. Preserve the separation between scientific SI time and renderer/client playback duration.

### #2 Electrostatic Field Laboratory

Implemented in the current development stack:

- `spectra/showcases/electrostatic_lab.py`
- public exports in `spectra/showcases/__init__.py`
- `tests/test_electrostatic_lab_showcase.py`
- `examples/blender_electrostatic_lab.py`
- `examples/blender_electrostatic_lab_smoke.py`
- `docs/ELECTROSTATIC_LAB_VALIDATION_HANDOFF.md`

Concept:

`+q/-q point sources -> conservative deposition -> generic 3D Poisson -> V field -> E=-grad(V) -> potential slice + batched E vectors + field lines -> quantitative presentation -> Blender`

Scientific/display contract:

- physical potential remains `V [V]`;
- potential Surface carries a vertex scalar `electric_potential` with `VOLT`;
- presentation uses `COOLWARM` with a zero-centered symmetric range;
- E-vector length is display scaling only;
- sources and field lines are renderer-neutral Scene primitives;
- no new electrostatic or Poisson solver was added;
- no presentation reveal is used in this first milestone, keeping the static scene simple and backend identity-friendly.

A test assumption tying field-line point count to a concrete fixed-step RK implementation was removed; tests should remain compatible with solver interchangeability.

### Important status

The Electrostatic showcase code/tests/Blender smoke are **written but not yet locally validated in this chat**. Do not claim PASS yet.

## Next action: validate #2 before more runtime code

On the local machine/agent, pull current `main`, then run approximately this gate:

```text
git status
git pull
python -m compileall spectra
pytest -q tests/test_electrostatic_lab_showcase.py \
  tests/test_potential_sources3d.py \
  tests/test_potential_field_views3d.py \
  tests/test_quantitative_presentation.py \
  tests/test_quantitative_shared_scale_and_legend.py

blender --background --python examples/blender_electrostatic_lab_smoke.py

pytest -q
```

Fix root causes only. Do not weaken tests just to obtain green. Report current SHA, targeted results, Blender smoke, full pytest count, initial failures, fixes, and blockers. If all green, record a new checkpoint before starting the next showcase.

## #3 Quantum Wavepacket — next implementation idea

Keep this first version intentionally bounded.

Use the existing 2D Schrödinger/complex-PDE stack. Build a normalized Gaussian wavepacket and produce a **static premium snapshot first**:

`Schrodinger2D semantics -> complex psi snapshot -> probability density |psi|^2 -> Surface height -> phase arg(psi) -> cyclic PHASE color -> presentation -> Blender`

Important design rules:

- scientific grid stays in **meters**;
- display geometry may explicitly map `1 nm -> 1 display unit` so Blender framing remains practical;
- probability density remains physical data, ideally tagged with the correct inverse-area unit/semantic quantity;
- phase is derived visualization data using `atan2(Im, Re)` and a fixed cyclic range `[-pi, +pi]`;
- phase/color derivation belongs to visualization/showcase composition, not a new quantum solver;
- do not silently rescale or overwrite the complex wavefunction;
- start static because the current generic Surface animation primarily tracks geometry; animated quantitative/phase attributes should be a separate generic capability rather than a showcase-specific hack.

After the static snapshot is green, decide whether to add generic animated VisualAttribute support. Only then make the probability/phase colors evolve through the Schrödinger timeline.

## After Quantum

Recommended showcase order:

1. Electrostatic validation/promotion.
2. Quantum static probability + phase showcase.
3. Thermoelastic heating/deformation showcase: temperature quantitative field + deformation + stress overlay using existing heat/thermoelastic domains.
4. Schwarzschild/geodesic showcase: compact central object + geodesic bundle + renderer-neutral annotations; keep it a visualization of the existing relativity/geodesic foundation, not a claim of full GR simulation.
5. CFD/reaction-diffusion later, after performance and dense-field presentation paths are mature.

For every showcase use the same discipline:

`existing scientific capability -> explicit view semantics -> generic Scene/Timeline -> quantitative/presentation policy -> Blender smoke -> full pytest -> checkpoint`

Do not add GPU/native numerical work, new renderer abstractions, or a second presentation engine as part of showcase work unless a validated generic gap proves it is necessary.

## Current continuation point

When resuming, first read this file and `docs/ELECTROSTATIC_LAB_VALIDATION_HANDOFF.md`. The immediate task is **validation of Electrostatic**, not additional feature expansion. If green, start the bounded static Quantum snapshot described above.
