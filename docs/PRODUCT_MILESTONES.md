# Spectra Science — Product Milestones

This document turns the architectural roadmap into product-level milestones with explicit exit criteria.

It is not a schedule. It is an ordering/quality map so the project does not confuse adding more scientific modules with becoming a usable scientific product.

## Milestone 0 — Semantic Engine Foundation

Status: largely achieved in the verified/implemented architecture.

Goals:

- renderer-independent Scene/Timeline;
- domain/capability system;
- math/physics/PDE composition;
- units/coordinates;
- Blender reference backend;
- dense primitives;
- transactional registration;
- automatic catalog discovery.

Recorded verified evidence includes the `acb9e056...` milestone with 224 tests and Blender 5.2 native smoke.

Exit concept:

> Scientific meaning exists independently from Blender and can compile to generic Scene primitives.

## Milestone 1 — Numerical Platform

Current large post-baseline development batch targets this milestone.

Goals:

- stable solver roles;
- multiple implementations;
- fixed/adaptive selection;
- solver policies/fallback;
- numerical provenance;
- experiments;
- sensitivity;
- uncertainty;
- calibration;
- convergence;
- reproducible artifacts/traces.

Exit criteria:

- current full suite green;
- catalog/provider graph green;
- RK4/Heun/RK45 reference cases green;
- solver policy/provenance green;
- experiment artifact round-trip green;
- high-level domains work through role dispatch.

No GPU is required for this milestone.

## Milestone 2 — Premium Presentation Foundation

Goals:

- renderer-neutral presentation semantic types;
- initial presets:
  - analysis;
  - publication;
  - presentation;
  - cinematic;
  - dark_lab;
- camera fit/policies;
- title/time/annotations;
- presentation-owned deterministic IDs;
- basic presentation composer extending `spectra.presentation`.

Exit criteria:

- base Scene remains unchanged scientifically;
- presentation variants compose deterministically;
- MemoryBackend can inspect enriched Scene;
- presentation-only changes do not trigger solve.

## Milestone 3 — Quantitative Visual Language

Goals:

- sequential/diverging/cyclic/categorical color scales;
- explicit range/center/clamp policy;
- legends tied to the same scale definition;
- axes/units;
- display sampling metadata;
- visual design system consistency.

Exit criteria:

- publication-quality quantitative interpretation possible without Blender-specific scientific code;
- scalar/vector/phase scenes use correct color semantics;
- shared-range comparisons supported;
- color/legend tests deterministic.

## Milestone 4 — Five Canonical Premium Scenes

Recommended first five:

1. electrostatic field laboratory;
2. Maxwell wave;
3. quantum probability + phase;
4. thermoelastic solid;
5. Schwarzschild/geodesic scene.

Each should support at least analysis/publication/cinematic variants where scientifically appropriate.

Exit criteria:

- complete generic Scene + presentation intent;
- meaningful units/legends/axes;
- stable animation semantics;
- no Blender-specific science.

## Milestone 5 — Blender Premium Backend

Goals:

- high-quality theme/world;
- camera mapping;
- studio/analysis lighting;
- quantitative material/color mapping;
- legends/text/axes;
- reveal/presentation animation;
- deterministic ownership/cleanup;
- incremental identity preserved.

Exit criteria based on `BLENDER_PREMIUM_ACCEPTANCE.md`:

- canonical scenes visually coherent;
- no resource leaks;
- preset switching safe;
- dense data stays batched;
- quantitative colors match legends;
- Blender 5.2+ native validation passes.

## Milestone 6 — Dense Rendering and Large-Data Presentation

Goals:

- Geometry Nodes/attributes or equivalent optimized dense representation;
- PointCloud/vector glyph instancing;
- per-instance color/scale;
- display LOD;
- improved update latency;
- large scalar-field presentation strategy.

Exit criteria:

- object count remains O(1)-style for dense primitives;
- meaningful improvement over current 10k reference path;
- no identity/cleanup regression;
- visual LOD does not alter solver data.

## Milestone 7 — Stable Public SDK

Goals:

- curated `spectra.sdk` facade;
- public API classifications;
- sample extension package works against documented API;
- capability/domain naming stable enough for external users.

Exit criteria:

- sample optics-style extension can be implemented without private imports;
- plain-Python SDK import requires no Blender/GPU;
- API stability/deprecation rules documented/tested.

## Milestone 8 — External Plugin Ecosystem

Goals:

- `PluginDescriptor`;
- explicit plugin list/loading;
- compatibility checks;
- enable/disable;
- deterministic conflict diagnostics;
- later Python entry-point discovery.

Exit criteria:

- third-party package adds domains without editing built-in manifests;
- broken/disabled plugin does not break base engine;
- project can report missing plugin dependency safely;
- no arbitrary code auto-install from project files.

## Milestone 9 — Spectra Project Format

Goals:

- durable renderer-independent project envelope;
- project metadata;
- scientific model records;
- solver policies;
- experiment references;
- presentation variants;
- external resource references;
- revision/invalidation model.

Exit criteria:

- project save/load round-trip;
- schema/version validation;
- one solution can feed multiple presentation variants;
- `.blend` is optional derived renderer state rather than scientific source of truth.

## Milestone 10 — Native CPU Numerical Provider

Recommended first target:

```text
ode.first_order / rk4.native_cpu
```

Goals:

- prove provider ABI/buffer boundary;
- parity with reference RK4;
- role selection/provenance;
- measurable speedup on suitable workload classes.

Exit criteria:

- canonical ODE cases parity/convergence;
- high-level PDE/mechanics runs unchanged;
- provider selectable/fallback-safe;
- native lifecycle/resource handling clean.

## Milestone 11 — Numerical Buffer Runtime

Goals:

- typed contiguous scalar/vector/grid buffers;
- explicit ownership/copy semantics;
- host/native mapping;
- memory/copy measurement.

Exit criteria:

- first native provider demonstrates the abstraction is useful;
- reference semantics remain ergonomic;
- no unnecessary universal buffer conversion tax.

## Milestone 12 — GPU Numerical Execution

Initial targets:

- batched ODE;
- Laplacian/gradient/divergence;
- simple diffusion/transport kernels.

Exit criteria:

- parity/reference cases;
- precision/provenance correct;
- host-device transfer measured separately;
- clear performance crossover;
- GPU-first policy/fallback works;
- scientific domains unchanged.

## Milestone 13 — Remote/HPC Execution

Goals:

- execution request/worker contract;
- capability negotiation;
- resource staging;
- job lifecycle;
- stale-result protection;
- remote provenance.

Exit criteria:

- same semantic problem runs locally/remotely;
- result plugs into same view/presentation pipeline;
- project revision prevents stale overwrite;
- approved plugin/provider policy enforced.

## Milestone 14 — Standalone/WebGPU Product

Goals:

- standalone project UI;
- WebGPU renderer consuming generic Scene/presentation;
- project browser;
- result/view/presentation workflows;
- interactive data inspection.

Exit criteria:

- same Spectra project can open outside Blender;
- scientific engine is shared, not duplicated;
- Blender and standalone client render the same semantic results through different backends.

## Milestone 15 — Advanced Scientific Solvers

Only after engine/product foundations are strong.

Potential tracks:

- production-grade sparse/multigrid solvers;
- unstructured FEM;
- advanced CFD;
- FDTD/PML;
- plasma/materials/optics modules;
- adaptive meshes;
- distributed/HPC solvers.

Each should enter as new scientific/numerical capabilities, not monolithic product rewrites.

## Parallel tracks

Some tracks may progress independently after clean checkpoints:

```text
Presentation/UI track
Numerical performance track
Scientific-domain expansion track
Plugin/SDK track
Remote infrastructure track
```

They must continue to meet at stable contracts rather than editing the same central assumptions in parallel.

## Milestone discipline

For cross-cutting runtime milestones:

```text
implement
 -> targeted tests
 -> full suite
 -> native Blender/provider validation when affected
 -> record verified commit/status
 -> continue
```

Documentation/spec work can proceed between checkpoints without claiming runtime verification.

## Product readiness ladder

A useful coarse product ladder:

### Engine demonstrator

Correct scientific computations + renderer-independent Scene + Blender reference backend.

### Technical alpha

Numerical platform + premium presentation foundation + canonical scenes.

### Creator/research alpha

Premium Blender backend + project workflows + stable SDK beginnings.

### Beta

Project format + plugin ecosystem + dense rendering + stronger solver performance + standalone/client workflows.

### Broader production

Supported-scope solvers/backends/project lifecycle/security/compatibility qualified for real users.

## Success criterion

Spectra should progress by turning stable architecture into increasingly complete user workflows, not merely by increasing the number of scientific modules. A milestone is complete only when the layer becomes dependable enough for the next layer to build on it without bypassing its contracts.
