# Spectra Science — Current Status

This document is the concise verified-status checkpoint for the current semantic engine.

## Current fully verified baseline

Commit:

```text
b9ca6b017cac83f45cc3864a88e219c848c12fc8
```

Reported local validation:

```text
compileall spectra: PASS
pytest: 276 passed
initial failures: 0
DomainCatalog / auto-discovery: PASS
119 domains
467 providers
numerical provenance / solver registry: PASS
presentation / Scene v5 / VisualAttribute: PASS
SDK / plugin / project layers: PASS
native-CPU-labelled RK4 provider boundary: PASS
Blender 5.2 targeted smoke: PASS
repo clean and synchronized with origin/main
```

This supersedes the earlier `acb9e056...` / 224-test baseline and the intermediate `00b5403...` validation-pending checkpoint.

## Verified runtime architecture at `b9ca6b0...`

### Scientific/domain platform

- renderer-independent semantic engine;
- automatic `...Domain` discovery and capability-provider graph;
- 119 discovered domains and 467 providers in the reported validation;
- capability-driven loading and transactional registration;
- generic mathematics, field, PDE, mechanics, fluid, solid, thermal, electromagnetism, quantum, relativity, chemistry, experiment, and multiphysics foundations.

### Numerical execution

Verified runtime includes:

- stable numerical roles such as `ode.first_order`;
- `NumericalSolverRegistry` implementation interchangeability;
- RK4 reference solver;
- Heun/RK2 reference solver;
- adaptive Dormand–Prince/RK45 reference solver;
- execution descriptors and problem-aware solver selection;
- ordered solver policies/fallback;
- fixed/adaptive numerical provenance;
- requested vs accepted step accounting;
- tracked method-of-lines composition;
- deterministic parameter sweeps and batching;
- convergence, sensitivity, uncertainty, calibration, ranking, and Pareto analysis;
- reproducibility/environment fingerprints;
- schema-versioned experiment artifacts and per-case traces.

### Native CPU provider boundary

The first provider-role proof is implemented and validated under:

```text
ode.first_order / rk4.native_cpu
```

It participates in the existing solver registry rather than introducing a parallel numerical runtime.

**Important:** at `b9ca6b0...`, `solve_native_rk4()` delegates to the existing Python `solve_rk4()` implementation. Therefore this milestone validates provider selection, capability wiring, execution metadata flow, and provenance plumbing; it does **not** yet validate a real C/C++/SIMD native RK4 kernel. Until that kernel exists, this implementation must not be presented as native performance acceleration.

The next performance checkpoint should either implement a real native kernel or change the execution metadata/name so provenance cannot imply native execution that did not occur.

### Presentation runtime

The renderer-neutral presentation layer is now runtime functionality rather than design-only documentation.

Verified areas include:

- presentation value/policy contracts;
- preset resolution;
- deterministic presentation resource identities;
- presentation composition over generic `Scene`;
- Scene-local camera framing;
- scientific/presentation timeline ownership rules;
- presentation resources without moving scientific semantics into Blender.

### Scene v5 / VisualAttribute

Current Scene schema is:

```text
spectra.scene v5
```

Visual attributes are generic renderer-neutral visualization data and can carry named scalar/vector/color channels with explicit association semantics.

Scene serialization/deserialization retains older-version compatibility according to the schema contract.

### SDK / plugin / project platform

Verified runtime now includes the first implementation of:

- curated SDK facade;
- plugin descriptor/registry/catalog composition;
- renderer-independent project document/runtime layer;
- reuse of existing reproducibility and experiment provenance instead of duplicate provenance formats.

These are foundation/runtime layers, not yet a complete marketplace, collaboration service, or polished standalone application.

## Blender 5.2 validation

Targeted Blender 5.2 smoke passed for:

- static scene mapping;
- animated wave geometry;
- animated electromagnetic fields;
- 10k `PointCloud` batching;
- 10k `VectorGlyphSet` batching;
- stable object/datablock identity;
- 100-frame leak test;
- cleanup/orphan behavior.

Dense batches remained one native representation each; they did not expand into 10,000 Blender objects.

Reported reference measurement from this validation run:

```text
create:          ~170.49 ms
combined update: ~89.95 ms
```

These numbers are commit/machine/run-specific Blender backend measurements. They are not GPU numerical-solver benchmarks and should not be generalized to every scene/workload.

## What is now verified vs still future

### Verified foundation/runtime

- semantic/capability engine;
- current numerical solver-role and experiment platform;
- Scene v5 visual attributes;
- first premium-presentation foundation;
- first curated SDK/plugin/project runtime layers;
- native-provider selection/provenance boundary proof for RK4;
- Blender 5.2 generic/incremental targeted behavior.

### Still future or materially incomplete

Examples:

- real native C/C++/SIMD RK4 execution behind the `rk4.native_cpu` role;
- production-grade CFD/RANS/LES/AMR;
- full industrial FEM/contact/plasticity/fracture/shells/beams;
- production RF/FDTD/PML/dispersive electromagnetics;
- quantum chemistry/DFT/many-body stack;
- real GPU numerical provider and device-resident PDE pipeline;
- advanced Blender Geometry Nodes visual-attribute pipeline where needed;
- full screen-space legend/layout/volume presentation system;
- mature external plugin entry-point ecosystem/marketplace;
- collaborative project server;
- remote/HPC worker implementation at product scale;
- standalone/WebGPU product surface and polished end-user UI.

## Next engineering direction

The old pending-validation gate is closed.

Further work should branch from `b9ca6b0...` as the verified runtime baseline and proceed in bounded checkpoints rather than another unvalidated mega-batch.

High-value next tracks are:

```text
Presentation depth
  -> richer quantitative legends/layout
  -> Blender visual-attribute/material realization
  -> canonical premium showcase scenes
  -> dense/Geometry Nodes optimization where evidence requires it

Performance
  -> replace the current Python RK4 wrapper with real native CPU execution
  -> typed numerical buffers/batching
  -> GPU solver/provider
  -> device-resident grid/PDE paths

Product
  -> strengthen SDK/plugin/project APIs
  -> headless/CLI/export workflows
  -> standalone/WebGPU surface
  -> later remote/HPC/collaboration
```

Do not mix all tracks into one foundational refactor unless a shared boundary genuinely requires it.

## Repository policy

GitHub Actions remains intentionally absent. Do not recreate it unless explicitly requested.

Generated caches, native build outputs, renders, releases, and local artifacts do not belong in source control.

## Success criterion

The repository should continue to make three things explicit:

1. what is scientifically/architecturally implemented;
2. what has actually been validated at a concrete commit;
3. what remains reference/foundation work versus production-grade capability.

For the current runtime milestone, the verified baseline is `b9ca6b017cac83f45cc3864a88e219c848c12fc8`.