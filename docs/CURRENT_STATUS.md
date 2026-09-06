# Spectra Science — Current Status

This file records the latest verified runtime checkpoint and the next bounded development milestone.

## Current fully verified baseline

Commit:

```text
183b8aa869f1643462fbfb00193e109d65c323e7
```

Reported local/native validation:

```text
repo clean/synced: PASS
compileall spectra: PASS
pytest: 300 passed
initial source failures: 0
validation-environment issue: setuptools missing; installed, native extension rebuilt successfully
DomainCatalog / auto-discovery: PASS
119 domains
468 providers
Scene v5 / Track.owner: PASS
quantitative shared scale: PASS
legend / axes / annotations: PASS
presentation recomposition / duration: PASS
SDK / plugin / project layers: PASS
native extension build: PASS
NATIVE_CPU_AVAILABLE: True
native/reference RK4 parity: PASS — max error 0.0
RK4 convergence: PASS — ratios ~16.42, ~16.21
CPU-only selection/provenance: PASS
Python fallback truthfulness: PASS
Blender 5.2 quantitative smoke: PASS
existing Blender static/wave/EM smoke: PASS
GitHub Actions: absent
remaining blockers: none
```

This supersedes the earlier `b9ca6b0...` / 276-test baseline.

## Verified quantitative presentation

The renderer-neutral presentation layer now includes verified runtime support for:

- `VIRIDIS`, `MAGMA`, `COOLWARM`, and `PHASE` palettes;
- `DATA`, `FIXED`, and `SYMMETRIC` range policies;
- one Scene-wide shared quantitative range for one quantity role;
- explicit rejection of mixed units on one shared scale until an explicit conversion contract exists;
- scalar `VisualAttribute` -> deterministic `display_color` mapping;
- deterministic world-space quantitative legends;
- analysis XYZ axes;
- camera-facing title/subtitle/time annotations;
- deterministic presentation IDs;
- scientific-vs-presentation track ownership;
- presentation recomposition and duration recovery;
- Scene-v5 persistence of non-default `Track.owner` metadata.

Scientific scalar values and color mapping remain renderer-independent.

## Verified Blender quantitative path

`QuantitativeBlenderBackend` is now validated in Blender 5.2 for:

```text
Surface vertex display_color
    -> Blender FLOAT_COLOR / POINT mesh attribute

PointCloud instance display_color
    -> current batched mesh representation
    -> Blender FLOAT_COLOR / POINT mesh attribute
```

The targeted quantitative smoke verified:

- 300 distinct values;
- one PointCloud native object;
- one quantitative material;
- native mesh color attribute;
- per-value alpha;
- effective `attribute alpha × primitive opacity` behavior;
- color-only object/datablock/material identity preservation;
- opacity-only object/datablock/material identity preservation;
- cleanup PASS.

The existing static/wave/EM Blender smoke also remained green.

Current deliberate limitation:

```text
VectorGlyphSet -> existing Curve/color fallback path
```

High-cardinality VectorGlyphSet native attributes / Geometry Nodes remain a later optimization.

## Verified real native CPU RK4 provider

The stable numerical role remains:

```text
ode.first_order
```

with implementation:

```text
rk4.native_cpu
```

The optional CPython extension now built successfully and was validated as real CPU execution:

```text
NATIVE_CPU_AVAILABLE = True
execution.kind = cpu
backend = spectra.native_cpu
device = host-cpu
```

Validation confirmed:

- exact parity with the reference RK4 case used by the validation (`max error 0.0`);
- fourth-order convergence behavior;
- CPU-only solver selection;
- tracked execution provenance;
- truthful Python fallback behavior when the extension is unavailable.

Reference benchmark from the reported validation workload:

```text
Python reference RK4: 56.538 ms
native provider:       12.842 ms
observed speedup:      ~4.40×
```

This number is machine/problem/RHS-specific. It is evidence for this validation workload, not a universal RK4 speedup claim. The native loop still invokes Python RHS callbacks at each RK stage; typed/batched native buffers remain the next numerical-performance direction.

## Catalog/runtime checkpoint

At this baseline:

```text
119 domains
468 providers
300 tests
```

The extra provider relative to the previous baseline reflects the current validated runtime graph.

## Current architecture status

Verified runtime includes:

- renderer-independent semantic/capability engine;
- automatic domain discovery and provider graph;
- RK4/Heun/RK45 reference solvers;
- real optional native CPU RK4 provider plus truthful fallback;
- solver policies, problem-aware selection, execution descriptors, provenance;
- ODE/PDE and current scientific-domain foundations;
- experiments, batching, convergence, sensitivity, uncertainty, calibration, Pareto, reproducibility, artifacts/tracing;
- Scene v5 / VisualAttribute;
- quantitative presentation runtime;
- curated SDK/plugin/project runtime layers;
- Blender 5.2 generic, incremental, and quantitative targeted behavior.

## Next bounded milestone — five flagship premium scenes

The next product-visible track starts from this verified commit and should remain bounded rather than becoming another foundational rewrite.

Recommended order:

```text
1. Maxwell electromagnetic wave
2. Electrostatic field laboratory
3. Quantum probability + phase
4. Thermoelastic solid
5. Schwarzschild geodesics
```

The purpose is to prove one reusable pipeline:

```text
scientific semantics / result
    -> explicit scientific view
    -> generic Scene + Timeline
    -> presentation intent
    -> quantitative/semantic visual policy
    -> premium presented Scene
    -> Blender now / future WebGPU later
```

Each showcase should have plain-Python structure tests first, then targeted Blender validation where relevant.

## Still future or materially incomplete

Examples:

- high-cardinality native/Geometry-Nodes `VectorGlyphSet` realization;
- fully screen-space legend/layout system;
- volume rendering primitive semantics;
- typed/batched native numerical buffers that reduce Python callback overhead;
- native grid/PDE kernels;
- GPU numerical provider;
- device-resident PDE pipeline;
- industrial CFD/RANS/LES/AMR;
- production FEM/contact/plasticity/fracture/shells/beams;
- production RF/FDTD/PML/dispersive electromagnetics;
- quantum chemistry/DFT/many-body stack;
- standalone/WebGPU polished product;
- production remote/HPC/collaboration services.

## Repository policy

GitHub Actions remains intentionally absent. Do not recreate it unless explicitly requested.

Generated `.pyd`, `.so`, `.dll`, `.dylib`, build/wheel outputs, caches, renders, and releases do not belong in source control.

## Success criterion

Keep three things explicit at every checkpoint:

1. what is implemented;
2. what has actually been validated at a concrete commit;
3. what remains reference/foundation work versus production-grade capability.

For the current runtime milestone, the verified baseline is:

```text
183b8aa869f1643462fbfb00193e109d65c323e7
```
