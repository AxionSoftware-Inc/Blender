# Black-Hole Geodesics Flagship — Validation Handoff

## Status

This document is a promotion gate for the canonical Schwarzschild/null-geodesic showcase.

The implementation is intentionally a bounded product/integration layer on top of existing Spectra capabilities. It has **not** been promoted to a verified checkpoint merely because these files exist in `main`.

Validate the current checkout/HEAD. Do not assume any SHA in older handoff documents is still current.

## What this showcase must prove

Scientific pipeline:

```text
Schwarzschild mass
    -> Schwarzschild metric in (ct, r, theta, phi)
    -> generic numerical Christoffel symbols
    -> generic selectable ODE-backed geodesic solver
    -> null geodesic solutions
    -> explicit equatorial projection
       x = (r/r_s) cos(phi)
       y = (r/r_s) sin(phi)
    -> renderer-neutral Scene
    -> presentation composer
    -> Blender backend
```

The showcase must not contain a hand-coded trajectory equation or a Blender-side relativity formula.

## Files in scope

```text
spectra/showcases/black_hole_geodesics.py
tests/test_black_hole_geodesics_showcase.py
examples/blender_black_hole_geodesics.py
examples/blender_black_hole_geodesics_smoke.py
spectra/showcases/__init__.py
```

Underlying reused capabilities that should remain unchanged unless a genuine root cause is found:

```text
spectra/domains/physics/general_relativity.py
spectra/domains/differential_geometry/domain.py
spectra/domains/differential_geometry/geodesics.py
spectra/domains/differential_equations/*
spectra/backends/blender/*
```

## Required validation sequence

From a clean/current repository checkout:

```bash
git status --short
git rev-parse HEAD
python -m compileall spectra
pytest -q tests/test_black_hole_geodesics_showcase.py
pytest -q
```

Then run Blender 5.2 headless:

```bash
blender --background --python examples/blender_black_hole_geodesics_smoke.py
```

Do not create GitHub Actions for this validation.

## Scientific acceptance checks

### Schwarzschild scale

- `SchwarzschildSpacetime.schwarzschild_radius` is the source of truth.
- solver coordinates remain physical length coordinates;
- display coordinates are explicitly normalized by `r_s` only after the geodesic solve;
- changing black-hole mass must not require changing the normalized display geometry logic.

### Null initial conditions

For the photon-sphere orbit and every scattering ray, verify at the initial point:

```text
g_mu_nu v^mu v^nu ~= 0
```

The metric itself, not a showcase approximation, should be used for this check.

### Photon-sphere orbit

The canonical circular null geodesic starts at:

```text
r = 1.5 r_s
theta = pi/2
```

Over one requested orbit it should remain close to `1.5 r_s` and advance by approximately `2 pi` in `phi` within the tolerance justified by the reference numerical solver.

Do not hard-code a required number of returned samples. `steps` is a solver request/hint and Spectra supports interchangeable fixed/adaptive implementations.

### Scattering rays

The current canonical impact parameters are all above the critical Schwarzschild capture value:

```text
b_critical / r_s = 3 sqrt(3) / 2
```

Each showcase ray should:

- begin at the configured outer radius;
- move inward;
- remain strictly outside the event horizon for the requested integration interval;
- turn back outward;
- increase azimuth through gravitational bending.

If a ray crosses the horizon during the configured interval, first determine whether this is a genuine solver/regression issue or simply an invalid showcase parameter before changing engine code.

### Projection

The renderer-neutral trajectory must be an explicit equatorial projection of the solved coordinate trajectory:

```text
x = (r/r_s) cos(phi)
y = (r/r_s) sin(phi)
z = 0
```

Blender must not infer or invent the projection.

## Architecture acceptance checks

- importing/building the scientific/base showcase outside Blender does not import `bpy`;
- the showcase consumes `geometry.solve_geodesic` instead of implementing another integrator;
- the generic geodesic role still dispatches through `ode.solve_first_order`;
- the event-horizon sphere and photon-sphere reference ring are context geometry only;
- presentation composition adds `presentation.*` resources without rewriting solver-generated paths;
- all IDs are deterministic and unique.

## Blender acceptance checks

The headless smoke should confirm:

- event horizon maps to one native mesh object;
- each geodesic maps to a native curve representation, not per-sample objects;
- native photon-orbit XY radius remains approximately `1.5` display units;
- scattering rays stay outside display radius `1.0` for this configured non-capture case;
- object count remains bounded;
- no-op `apply()` preserves representative object/datablock identity;
- destroy removes the Spectra collection/resources owned by the session.

## Root-cause policy

If validation fails:

1. reproduce the smallest failing path;
2. identify whether the fault is in showcase parameters/projection, generic geodesics, numerical solver selection, Scene composition, or Blender mapping;
3. fix the root cause;
4. do not weaken the scientific assertions merely to make the test green;
5. do not replace solver-generated geodesics with analytic/hard-coded display curves;
6. rerun the targeted test and Blender smoke;
7. then rerun full `pytest -q`.

## Promotion report

Report:

- current HEAD SHA;
- `compileall` result;
- targeted pytest count/result;
- full pytest count/result;
- Blender 5.2 smoke result;
- photon-orbit max radial drift in units of `r_s`;
- initial null-norm residual range;
- minimum radius reached by every scattering ray;
- native object count;
- whether object/datablock identity stayed stable;
- fixes made, if any;
- remaining blockers.

Only after these checks pass should this flagship be described as a verified Black-Hole Geodesics checkpoint.
