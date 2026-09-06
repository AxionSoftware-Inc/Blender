# Quantum 2D Showcase — implementation notes at chat handoff

This is not a claim of completed runtime implementation. It records the source audit and the safe next design so the work can resume without re-discovering the same constraints.

## Reuse these existing components

- `spectra/domains/physics/schrodinger2d.py`
- `spectra/domains/partial_differential_equations/complex2d.py`
- generic 2D scalar Surface compiler
- presentation composer
- quantitative visual attributes
- `ColorPalette.PHASE`

## Do not add

- a duplicate Schrödinger solver;
- a showcase-specific time integrator;
- Blender-specific quantum code in the scientific layer;
- a fake unit conversion that changes the physical PDE merely to make the camera comfortable;
- a 3D volume renderer as the first quantum milestone.

## Canonical case

Use a bounded 2D Gaussian free-particle wavepacket with non-zero mean momentum so phase structure is visible.

Recommended conceptual scientific source:

```text
ψ(x,y,0) = A exp(-((x-x0)^2 + (y-y0)^2)/(4σ^2)) exp(i(kx x + ky y))
```

The actual implementation should use existing normalization capability rather than relying on a hand-derived A if that avoids duplication.

## Scientific vs display coordinates

The physical electron problem is naturally nanometer-scale.

Keep:

- PDE coordinates in SI meters;
- time in SI seconds;
- mass as a dimension-safe `Quantity`;
- scientific ψ samples unmodified.

Introduce only a presentation/showcase mapping for geometry, e.g. conceptually:

```text
1 nm physical coordinate -> 1 display unit
```

Name that mapping explicitly in configuration. It is not a unit conversion inside the solver.

## Probability density

For every complex state:

```text
rho = |ψ|^2
```

Use rho as the scientific scalar attribute. For a 2D wavefunction normalized over x/y, rho conceptually carries inverse-area dimensional meaning. If the current Unit model does not yet expose an exact convenient inverse-square-meter constant, do not invent an incorrect unit. Preserve quantity identity and document the limitation until the unit type is represented correctly.

Surface height may use normalized display height:

```text
z_display = probability_height_scale * rho / max(rho)
```

That height is presentation geometry, not a physical length claim about rho.

## Phase

Derive:

```text
phase = atan2(Im ψ, Re ψ)
```

This is a view/presentation-derived scalar, not a new quantum solver capability.

Use the cyclic `PHASE` palette. Avoid linear VIRIDIS/COOLWARM for wrapped phase.

Potential design options:

- keep `probability_density` as the scientific scalar attribute;
- keep `phase` as a separate scalar visual attribute;
- derive `display_color` from phase explicitly;
- preserve both source attributes so downstream renderers can choose alternate presentation later.

## Timeline

The scientific Timeline must remain the true Schrödinger time interval. If that time is too short for a human-visible Blender animation, use client/backend playback-duration mapping like the Maxwell showcase rather than rewriting Timeline seconds.

## Acceptance tests to add

Python tests should verify at least:

- initial probability mass is approximately 1;
- final probability mass remains within the expected bounded reference tolerance;
- one topology-stable Surface represents the wavepacket;
- source probability-density values remain available after presentation;
- phase-derived color data has one color per vertex;
- cyclic phase mapping wraps consistently near -pi/+pi;
- scientific grid coordinates remain SI-scale while display vertices use the explicit display mapping;
- presentation does not mutate ψ source states;
- scientific timeline duration is unchanged by presentation;
- invalid display scale/config is rejected.

Avoid asserting an exact number of ODE time samples if solver selection may become adaptive.

## Blender smoke to add

Target:

- one animated Surface mesh;
- one quantitative/phase material;
- native color attribute per vertex;
- no per-vertex material explosion;
- start/mid/end object/datablock identity stable if current Surface incremental path supports value-only vertex/color updates;
- client playback mapping preserves scientific duration semantics;
- cleanup PASS.

If current Blender incremental Surface color updates require structural recreation, treat that as a backend issue to fix at the quantitative adapter layer rather than putting Blender logic in the quantum showcase.

## Promotion label

Until all of the above is implemented and validated, use:

**AUDITED / IMPLEMENTATION NOT YET COMPLETED**
