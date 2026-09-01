# Spectra Science — Canonical Showcase Scenarios

This document defines a small set of flagship scientific scenes that should exercise the full Spectra pipeline:

```text
semantic problem
    -> numerical/scientific computation
    -> fields / trajectories / diagnostics
    -> generic Scene + Timeline
    -> presentation policy
    -> Blender or another renderer
```

These scenarios are not only marketing demos. They are integration targets that reveal whether scientific composition, presentation, animation, batching, and backend mapping work together cleanly.

## General acceptance rules

Every showcase should satisfy:

1. scientific inputs are explicit;
2. the scientific result exists independently of Blender;
3. units are preserved;
4. visualization semantics are explicit;
5. dense data remains batched;
6. presentation styling does not alter solver data;
7. camera/light/material choices are presentation policies;
8. animation distinguishes scientific time from presentation reveal time;
9. diagnostics can be displayed without renderer-side recomputation;
10. the same base Scene could be consumed by another renderer.

A showcase must not contain hidden Blender-only formulas that make the demo work.

---

## 1. Electrostatic field laboratory

### Purpose

Demonstrate potential-field composition and dense vector/field-line visualization.

### Scientific pipeline

```text
point charges
    -> generic point deposition
    -> charge density grid
    -> Poisson3D
    -> electric potential V
    -> E = -grad(V)
    -> PotentialField3D
```

### Scene content

- source charge markers;
- potential scalar slice or multiple slices;
- batched `VectorGlyphSet` for E;
- integral-curve field lines;
- compact potential legend with volts;
- electric-field vector scale with N/C;
- optional charged test-particle trajectory.

### Presentation presets

- `analysis`: axes, full legends, numerical diagnostics;
- `presentation`: source reveal -> potential -> arrows -> field lines;
- `cinematic`: dark environment, controlled luminous field emphasis, orbit camera.

### Quality checks

- field-line direction consistent with E;
- positive/negative source distinction remains accessible without relying on glow only;
- field arrow display density is independent of solver grid resolution;
- particle motion uses mechanics/Lorentz pipeline rather than presentation animation.

---

## 2. Maxwell wave propagation

### Purpose

Demonstrate time-dependent vector fields, scientific time, batched animation, and EM diagnostics.

### Scientific pipeline

```text
Maxwell3D initial/source problem
    -> E(x,y,z,t)
    -> B(x,y,z,t)
    -> energy / divergence / Poynting diagnostics
```

### Scene content

- E `VectorGlyphSet`;
- B `VectorGlyphSet`;
- propagation axis/reference plane;
- optional Poynting vectors;
- time indicator;
- compact energy/divergence diagnostic panel.

### Presentation sequence

```text
1. reveal propagation axis
2. reveal E field
3. reveal B field
4. reveal E/B relationship annotation
5. begin scientific-time evolution
6. optionally reveal Poynting flow
```

### Quality checks

- E/B geometry changes with sampled scientific time;
- stable primitive IDs/datablocks under incremental backend;
- no native object-count growth during playback;
- colors and legend clearly distinguish E and B.

---

## 3. Quantum wavepacket / Schrödinger 3D

### Purpose

Demonstrate complex scientific state with multiple explicit valid views.

### Scientific pipeline

```text
complex initial wavefunction
    -> Schrödinger evolution
    -> psi(x,y,z,t)
    -> probability density |psi|^2
    -> probability current
    -> continuity diagnostics
```

### Scene content

A primary explicit view selected from:

- probability-density slice;
- magnitude slice;
- phase visualization;
- current vector field;
- combined density + current.

### Presentation rules

- probability density uses non-negative sequential scale;
- phase uses cyclic scale;
- phase and magnitude are not conflated into an arbitrary renderer effect;
- units/normalization diagnostics available in analysis mode.

### Quality checks

- visualization view explicitly states which complex component is shown;
- normalization/probability diagnostics come from engine computation;
- display sampling is distinct from numerical grid resolution.

---

## 4. Incompressible flow around a conceptual obstacle

### Purpose

Demonstrate CFD composition, pressure/velocity semantics, diagnostics, and pathlines.

### Scientific pipeline

```text
velocity/pressure state
    -> advection
    -> diffusion
    -> pressure Poisson projection
    -> incompressible-flow history
    -> continuous velocity/pressure fields
    -> vorticity / invariants / pathlines
```

### Scene content

- obstacle/context geometry represented generically where available;
- velocity glyphs or streamlines;
- animated pathlines;
- pressure scalar slice/surface;
- vorticity visualization;
- max-divergence/CFL indicators.

### Presentation sequence

```text
geometry/context
    -> inlet/flow direction
    -> velocity field
    -> pressure
    -> pathlines
    -> vorticity focus
```

### Quality checks

- pressure colors have quantitative legend;
- velocity arrow scale is explicit;
- streamlines/pathlines are not confused;
- presentation decimation does not alter solver state;
- reference solver is labeled as such in analysis/provenance modes.

---

## 5. Thermoelastic solid heating

### Purpose

Demonstrate true multiphysics composition and deformed animated geometry.

### Scientific pipeline

```text
volumetric heat source
    -> heat conduction
    -> temperature field
    -> thermal strain
    -> elastic stress / elastodynamics
    -> displacement history
```

Possible heat sources:

```text
J dot E electrothermal heating
or
reaction enthalpy thermochemical heating
```

### Scene content

- undeformed/reference outline;
- deformed batched lattice/solid representation;
- temperature scalar coloring;
- displacement vectors optionally;
- von Mises stress slice/view;
- kinetic/strain/thermal diagnostic summary.

### Presentation sequence

```text
1. reveal solid
2. reveal heat source
3. show temperature spreading
4. reveal deformation
5. switch/focus to stress
```

### Quality checks

- deformation display scale, if exaggerated, is clearly labeled as presentation scale;
- actual displacement values remain unchanged;
- temperature/stress legends use correct units;
- scientific and presentation scaling are never conflated.

---

## 6. Reaction-diffusion pattern formation

### Purpose

Demonstrate chemistry + coupled PDE + experiment-ready parameterization.

### Scientific pipeline

```text
ReactionNetwork
    -> local source rates
    + species diffusion
    -> coupled reaction-diffusion PDE3D
    -> concentration fields over time
```

### Scene content

- selected species concentration slice(s);
- optional side-by-side species comparison;
- concentration legend in mol/m^3;
- time indicator;
- reaction parameter summary;
- optional experiment parameter trace.

### Presentation possibilities

- `analysis`: multiple species side by side;
- `presentation`: explain reaction then reveal pattern formation;
- `cinematic`: minimal annotations, smooth evolving scalar field.

### Quality checks

- species identity stays categorical and clear;
- concentration is never represented with a diverging scale unless scientifically justified;
- reaction kinetics are computed once in the chemistry network and reused spatially.

---

## 7. Schwarzschild / black-hole geodesics

### Purpose

Demonstrate differential geometry, relativity, explicit projection semantics, and premium trajectory presentation.

### Scientific pipeline

```text
metric tensor
    -> inverse metric
    -> Christoffel symbols
    -> geodesic ODE
    -> trajectory in chosen coordinate representation
    -> explicit display projection
```

### Scene content

- central reference object/context marker;
- one or multiple geodesic trajectories;
- optional local frame/reference grid;
- labels for initial conditions;
- explicit projection/coordinate annotation;
- optional proper-time or affine-parameter indicator.

### Presentation sequence

```text
1. establish coordinate/context frame
2. reveal initial condition
3. draw geodesic
4. reveal comparison geodesic(s)
5. orbit/focus camera without changing trajectory
```

### Quality checks

- renderer does not invent higher-dimensional projection;
- coordinate/projection semantics are explicit;
- camera orbit is presentation-only;
- trajectory is generated by the geodesic solver, not hand-keyframed.

---

## 8. Solver laboratory / numerical experiment dashboard

### Purpose

Demonstrate that Spectra is a computation platform, not only a scene renderer.

### Scientific pipeline

```text
one semantic ODE/PDE problem
    -> multiple solver implementations
    -> tracked runs
    -> convergence / error metrics
    -> ExperimentResult
    -> experiment views
```

### Scene content

- convergence log-log curve;
- solver comparison response curve;
- runtime/error or cost/error Pareto plot when metrics exist;
- selected implementation labels;
- environment fingerprint/provenance badge in analysis mode.

### Presentation sequence

- reveal reference/expected solution;
- add solver results;
- add error/convergence comparison;
- highlight selected/preferred implementation.

### Quality checks

- numerical results and provenance are engine-generated;
- plots compile to generic Scene primitives;
- no renderer-specific charting dependency is required.

---

## 9. Coupled electrothermal charged-particle demonstration

### Purpose

Exercise several independent capability chains in one coherent scene.

### Scientific pipeline

```text
Maxwell / electric field
    -> charged particle Lorentz trajectory

current + electric field
    -> J dot E heat source
    -> temperature field
```

### Scene content

- E/B vectors;
- charged particle path;
- temperature surface/slice;
- source/current annotation;
- optional Poynting/energy diagnostics.

### Quality checks

- particle path and thermal field share field semantics but independent solvers where appropriate;
- one visualization/presentation system composes both;
- native renderer sees only generic Scene content.

---

## 10. Parameter-design exploration

### Purpose

Demonstrate sensitivity, uncertainty, calibration, ranking, and Pareto analysis on a real scientific module.

Candidate examples:

- heat conductivity vs peak temperature;
- diffusion coefficient vs pattern scale;
- charge/source strength vs particle deflection;
- elastic modulus vs displacement/stress;
- flow parameter vs energy/divergence diagnostic.

### Scene content

- parameter response curve;
- sensitivity chart;
- uncertainty summary;
- calibrated/best candidate highlight;
- Pareto front for multi-objective problem;
- selected scientific result shown alongside experiment view.

### Quality checks

- metrics remain unit-aware;
- experiment environment/provenance is trackable;
- visualization is renderer-neutral;
- selected parameter case can feed back into the same scientific Scene pipeline.

---

## Premium demo suite recommendation

The first polished public-facing suite should likely include five scenes:

```text
1. Electrostatic field laboratory
2. Maxwell wave propagation
3. Quantum wavepacket
4. Thermoelastic multiphysics
5. Black-hole geodesics
```

Together they demonstrate:

- scalar fields;
- vector fields;
- trajectories;
- complex fields;
- PDE time evolution;
- multiphysics;
- geometry/relativity;
- animation;
- dense batching;
- renderer independence.

CFD and reaction-diffusion should follow as numerical/performance quality matures.

## Showcase implementation rule

A showcase is successful only if removing Blender-specific code still leaves a complete scientific computation and renderer-neutral Scene description.

The premium renderer should make the result beautiful; it must not be the reason the science works.
