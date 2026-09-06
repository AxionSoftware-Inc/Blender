# Spectra Science — Electrostatic Flagship Validation Handoff

Status: **Electrostatic Field Laboratory implemented on top of the pending Maxwell flagship stack; validation pending**.

Last fully verified baseline:

```text
183b8aa869f1643462fbfb00193e109d65c323e7
```

That baseline reported 300 passing tests, 119 domains / 468 providers, real compiled native RK4, and Blender 5.2 quantitative/native smoke PASS.

The Maxwell batch after that baseline is still separately pending. If validating the current combined head, run both the Maxwell and Electrostatic handoffs before promoting the stack.

## Purpose

This is flagship #2. It must prove that existing electrostatic, generic potential-field, quantitative-presentation, and Blender-native paths compose into one reusable product scene without introducing a showcase-specific solver.

Scientific pipeline:

```text
typed PointChargeSource3D (+q, -q)
    -> conservative cloud-in-cell source deposition
    -> ElectrostaticPotentialProblem3D
    -> generic 3D Poisson solve
    -> V [volt]
    -> E = -grad(V) [N/C]
    -> common PotentialField3D
    -> scalar slice / vector view / field-line bundle
    -> generic Scene
    -> quantitative presentation
    -> QuantitativeBlenderBackend
```

No Coulomb/Poisson algorithm is duplicated in `spectra.showcases`.

## New public showcase API

```text
spectra.showcases.ElectrostaticLabShowcaseConfig
spectra.showcases.build_electrostatic_lab_base_scene
spectra.showcases.build_electrostatic_lab_scene
```

Canonical defaults use a symmetric dipole inside a finite fixed-boundary laboratory volume.

## Scientific/display semantics

The scalar slice carries a Scene-v5 attribute:

```text
name        = electric_potential
association = vertex
kind        = scalar
quantity_id = electric_potential
unit        = VOLT
```

The presented scene uses:

```text
palette    = COOLWARM
range mode = SYMMETRIC
center     = 0 V
```

This is a signed physical quantity. Presentation must never replace the source scalar values with normalized color coordinates.

Electric-field arrows use `vector_display_scale` only for arrow geometry. The underlying model remains `E [N/C]`.

Field lines use the common integral-curve capability in normalized tracing mode. Their accepted point count must not be treated as a fixed scientific contract because the ODE implementation is interchangeable.

## Deliberate presentation choice

This first electrostatic milestone disables staggered reveal even though the scene is static.

Reason: the milestone is intended to validate quantitative Surface realization and field/view composition without mixing native identity questions with presentation-opacity animation. A richer reveal can be added after the static flagship is green.

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

Import outside Blender:

```text
spectra.showcases
spectra.showcases.electrostatic_lab
```

No eager `bpy` import.

### G2 — targeted plain-Python tests

Run at minimum:

```text
tests/test_electrostatic_lab_showcase.py
tests/test_potential_sources3d.py
tests/test_potential_field_views3d.py
tests/test_electrostatic_potential_2d.py
tests/test_poisson_cross_domain_reuse.py
tests/test_quantitative_presentation.py
tests/test_quantitative_shared_scale_and_legend.py
```

Also rerun the Maxwell targeted set if validating the combined current head.

Root-cause fixes only.

### G3 — electrostatic scientific invariants

For the canonical/small validation configuration confirm:

- source charges are equal magnitude and opposite sign;
- +q is on negative x and -q is on positive x;
- deposited total charge is approximately zero;
- Poisson solve reports `converged=True`;
- residual is <= requested tolerance;
- potential model exposes `VOLT` scalar output;
- electric field exposes `NEWTON_PER_COULOMB` output;
- z=0 potential slice has both positive and negative values;
- symmetric geometry yields approximately antisymmetric potential extrema;
- potential near +q is positive;
- potential near -q is negative;
- E at the dipole center points from +q toward -q;
- scalar values remain unchanged by presentation colorization.

### G4 — Scene/view invariants

Confirm:

- one potential `Surface`;
- one batched electric `VectorGlyphSet`;
- vector instance count equals `vector_samples ** 2`;
- field-line count equals configured seed count;
- two source `Point` primitives exist;
- quantitative potential attribute is vertex-associated and carries `VOLT`;
- base Scene is static (`Timeline.duration == 0`);
- presented Scene remains static because reveal is disabled;
- presentation adds deterministic camera/title/axes/legend resources;
- quantitative legend range is symmetric about 0;
- legend shows volts;
- no per-value material explosion exists in generic Scene semantics.

### G5 — full pytest

```text
pytest -q
```

PASS required. Record actual count; do not reuse 300 or any earlier count.

### G6 — DomainCatalog

Run the normal catalog/provider probe.

`Spectra.showcases` lives outside `spectra.domains`, so adding this product composition module should not itself create a new Domain/provider.

Record actual counts. Do not force 119 / 468 if another legitimate development change altered them.

### G7 — Blender 5.2 electrostatic smoke

Run:

```text
blender --background --python examples/blender_electrostatic_lab_smoke.py
```

Required behavior:

- potential Surface exists as one Blender mesh object;
- native `spectra_display_color` FLOAT_COLOR/POINT attribute exists;
- native color attribute length equals Surface vertex count;
- potential Surface uses one quantitative material;
- E vectors remain one batched Curve representation;
- Curve spline count equals vector instance count;
- configured field-line objects exist;
- +q and -q source objects exist;
- no object-count explosion;
- static re-apply preserves potential Surface object/datablock identity;
- static re-apply preserves E VectorGlyphSet object/datablock identity;
- cleanup removes the Spectra-owned collection.

### G8 — quantitative regression

Rerun the existing quantitative Blender smoke:

```text
examples/blender_quantitative_smoke.py
```

The flagship must not regress the already-verified 300-value PointCloud path, alpha/opacity semantics, or quantitative identity behavior.

### G9 — source-boundary audit

Confirm:

- no electrostatic solver exists in `spectra/showcases`;
- source deposition is reused through capability registration;
- Poisson is reused through `pde.solve_poisson_3d` indirectly via electrostatic domain;
- E is derived by the existing electrostatic domain as `-grad(V)`;
- field lines reuse the common field-dynamics bundle solver;
- no `bpy` entered scientific/showcase construction;
- `VOLT` scalar values are retained upstream of color mapping;
- vector display scaling is explicit and presentation-only;
- E vectors remain batched rather than one Scene/Blender object per arrow.

## Known deliberate limitations

This milestone does not claim:

- infinite-domain analytic Coulomb accuracy at the finite fixed boundary;
- singular point-charge resolution below the numerical grid scale;
- adaptive mesh refinement;
- equipotential contour primitive support;
- Geometry-Nodes VectorGlyphSet realization;
- per-vector quantitative native color attributes;
- electrostatic conductor/boundary-condition CAD workflows;
- production electrostatics/FEM capability.

The canonical scene is a reference scientific/product integration laboratory, not a production electrostatics package.

## Promotion rule

Do not promote this flagship independently while an earlier stacked flagship remains unvalidated.

For the current combined development head, promotion requires:

1. Maxwell handoff applicable gates PASS;
2. Electrostatic handoff applicable gates PASS;
3. full pytest PASS;
4. catalog probe PASS;
5. both targeted Blender smokes PASS;
6. repo clean/synced at a recorded SHA.

Final report should include:

```text
Final SHA
repo clean/synced
compileall
full pytest + actual count
initial failures
DomainCatalog domains/providers
Maxwell gate status if combined validation
electrostatic Poisson converged/residual
deposited net charge
potential min/max + units
E center direction
Surface/vector/field-line counts
Blender native Surface attribute/material count
Blender VGS spline count
static identity result
quantitative regression result
cleanup result
root fixes
remaining limitations
GitHub Actions absent
```
