# Spectra Science — Thermoelastic Heated-Bar Flagship Validation Handoff

Status: **flagship #4 implemented; local Python + Blender validation pending**.

Do not promote the current development head to `VERIFIED GREEN` from repository inspection alone. The repository intentionally has no GitHub Actions substitute for the required local/native validation gate.

## Purpose

This flagship demonstrates a bounded multiphysics composition without creating a second heat or elasticity solver stack:

```text
3D transient heat conduction in SI
    -> final temperature field [K]
    -> existing thermoelastic thermal-strain capability
    -> slender free-bar axial strain interpretation
    -> integrated physical elongation [m]
    -> explicitly exaggerated display deformation
    -> renderer-neutral Surface + reference outline
    -> quantitative temperature presentation
    -> QuantitativeBlenderBackend
```

The showcase lives in `spectra/showcases/thermoelastic_bar.py`. It reuses `physics.heat_conduction.solve3d` and `physics.thermoelasticity.thermal_strain`; it does not implement a new heat integrator or constitutive law.

## Public showcase API

```text
spectra.showcases.ThermoelasticBarShowcaseConfig
spectra.showcases.solve_thermoelastic_bar_showcase
spectra.showcases.build_thermoelastic_bar_base_scene
spectra.showcases.build_thermoelastic_bar_scene
```

## Scientific/display separation

The final Surface stores physical vertex attributes:

```text
temperature    -> quantity_id=temperature, unit=K
thermal_strain -> quantity_id=thermal_strain, unit=1
```

The physical free-bar elongation is computed before display deformation. `deformation_exaggeration` changes only Scene geometry. It must never rewrite temperature, strain, material data, solver time, or the reported physical elongation.

The undeformed outline remains in the Scene so the display exaggeration is visually explicit.

## Deliberate model scope

The current flagship uses a declared **slender free-bar approximation** after the 3D heat solve:

- axial thermal strain is sampled along the bar centerline from the existing isotropic thermoelastic capability;
- free axial displacement is integrated from the anchored left reference end;
- the displayed transverse expansion uses the same isotropic thermal strain;
- this is not a claim of a full constrained 3D thermoelastic stress solve.

A later flagship may compose full elasticity/elastodynamics, constraints, von Mises stress, and scientific-time deformation animation.

## Required validation sequence

### G0 — exact repository state

```bash
git status
git log -1 --oneline
git pull
```

Record the exact starting SHA and require a clean/synced tree before promotion.

### G1 — compile/import boundary

```bash
python -m compileall spectra
```

Outside Blender, importing these modules must not import `bpy`:

```text
spectra.showcases
spectra.showcases.thermoelastic_bar
```

### G2 — targeted plain-Python tests

Run at minimum:

```text
tests/test_thermoelastic_bar_showcase.py
tests/test_heat_thermoelastic3d.py
tests/test_quantitative_presentation.py
tests/test_quantitative_shared_scale_and_legend.py
```

Also rerun the earlier flagship targeted tests when promoting the combined head.

### G3 — scientific invariants

For a small deterministic validation configuration confirm:

- heat solution duration equals configured SI end time;
- temperature remains finite and positive;
- a positive hot-spot rise produces positive thermal strain;
- final free-bar elongation is positive;
- `temperature` remains in kelvin;
- `thermal_strain` remains dimensionless;
- no showcase-specific heat RHS, Laplacian, ODE integrator, or thermal-expansion constitutive law is introduced.

### G4 — presentation invariants

Confirm:

- the quantitative primary scalar is `temperature`;
- the automatic quantitative legend reports kelvin;
- presentation color mapping does not mutate the stored temperature or strain values;
- the undeformed outline remains separate from the deformed Surface;
- the result label reports actual elongation separately from display exaggeration;
- Scene scientific geometry is already composed before the Blender backend runs.

### G5 — full Python suite

```bash
pytest -q
```

PASS required. Record the actual test count and initial failure count. Do not reuse historical counts.

### G6 — DomainCatalog

Run the normal catalog/provider audit and record actual counts. The showcase itself is not a Domain and should not create new semantic providers merely by existing.

### G7 — Blender 5.2 thermoelastic smoke

Run:

```bash
blender --background --python examples/blender_thermoelastic_bar_smoke.py
```

Required native behavior:

- one quantitative thermoelastic Surface object;
- native `spectra_display_color` POINT attribute exists;
- native attribute sample count matches Surface vertex count;
- one quantitative material on the Surface;
- native deformed x-extent matches renderer-neutral Scene geometry;
- static no-op re-apply preserves object identity;
- static no-op re-apply preserves mesh datablock identity;
- quantitative color attribute remains after re-apply;
- cleanup removes the Spectra-owned collection.

### G8 — stacked Blender regressions

For combined-head promotion also rerun:

```text
examples/blender_quantitative_smoke.py
examples/blender_maxwell_showcase_smoke.py
examples/blender_electrostatic_lab_smoke.py
examples/blender_quantum_wavepacket_smoke.py
```

plus older static/incremental backend smokes used by the latest verified baseline when practical.

### G9 — source-boundary audit

Confirm:

- no `bpy` import in `spectra/showcases/thermoelastic_bar.py`;
- 3D heat solve remains in the heat-conduction domain;
- thermal strain remains provided by the thermoelasticity domain;
- actual elongation is computed before deformation exaggeration;
- presentation does not rewrite scientific scalar attributes;
- Blender performs realization only and contains no hidden thermoelastic formulas.

## Known deliberate limitations

This milestone does not claim:

- a general constrained 3D thermoelastic finite-element solver;
- contact, plasticity, fracture, creep, or nonlinear constitutive behavior;
- full 3D stress recovery for the showcase bar;
- von Mises stress visualization in this first flagship;
- scientific-time deformation animation;
- temperature-dependent material properties;
- production mesh adaptivity.

It is a canonical integration proof for heat conduction -> thermal strain -> physical free expansion -> renderer-neutral quantitative visualization.

## Promotion rule

Keep the status `IMPLEMENTED / PENDING VALIDATION` until all applicable Python, catalog, stacked flagship, and Blender smoke gates pass on one recorded local SHA.

Final promotion report should include:

```text
Final SHA
repo clean/synced
compileall
full pytest + actual count
initial failures
DomainCatalog domains/providers
heat-solve end time
temperature min/max + unit
thermal-strain min/max + unit
actual free elongation
display exaggeration
native quantitative attribute count
native mesh identity result
stacked Blender regression result
cleanup result
root fixes
remaining limitations
GitHub Actions absent
```
