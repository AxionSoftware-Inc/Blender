# Spectra Science — Post-Validation Implementation Plan

This document defines the recommended runtime implementation order **after** the current large numerical/experiments `main` batch completes its next full local validation.

The purpose is to avoid implementing several new foundational layers simultaneously and losing a clean verified checkpoint.

## Gate 0 — current validation

Before new runtime foundation work:

```text
python -m compileall spectra
pytest -q
DomainCatalog probe
targeted numerical/experiment regressions
```

must be green on the current head after any root fixes.

The Blender backend does not require a full native benchmark unless Scene/backend behavior changed, but ordinary Scene/backend regressions must remain green.

If the current batch is not green, fix that baseline before implementing the phases below.

---

## Phase 1 — renderer-neutral presentation semantics

Implement only the minimal immutable presentation contracts described in `PREMIUM_PRESENTATION_SYSTEM.md`.

Suggested initial types:

```text
PresentationPreset
PresentationTheme
CameraPolicy
ColorScalePolicy
LegendPolicy
AxesPolicy
AnnotationPolicy
AnimationPolicy
QualityPolicy
PresentationIntent
```

### Requirements

- no `bpy` imports;
- no renderer engine names in generic presets;
- immutable/value-oriented contracts;
- deterministic validation;
- small initial built-in preset set.

### Initial built-ins

```text
analysis
publication
presentation
cinematic
dark_lab
```

Do not implement every possible style feature at once.

### Exit criteria

- plain-Python tests;
- serialization strategy decided if presentation intent becomes persistent;
- no scientific-domain changes required merely to construct a preset.

---

## Phase 2 — presentation composer

Extend existing `spectra.presentation` rather than creating a parallel presentation engine.

Responsibilities:

```text
base Scene
+ PresentationIntent
    -> presentation-enriched Scene
```

Initial features:

- bounds-driven camera fit;
- deterministic background/theme resources where generic;
- basic light intent;
- time/title labels;
- staggered reveal composition;
- presentation-owned deterministic IDs.

Do not add Blender-specific native nodes yet.

### Exit criteria

- MemoryBackend can inspect resulting Scene;
- scientific primitive IDs remain stable;
- changing presentation does not recompute science;
- base Scene is not mutated destructively.

---

## Phase 3 — quantitative color scales and legends

Introduce renderer-neutral scalar/categorical/cyclic color policies.

Initial requirements:

- sequential;
- diverging with explicit center policy;
- cyclic phase;
- categorical;
- explicit range/clamp behavior;
- unit-aware legend metadata.

Color policy and legend must derive from the same range definition.

### Exit criteria

- scalar data can be displayed with deterministic legend;
- quantitative colors survive MemoryBackend/Scene inspection;
- presentation display range is distinct from solver data range/resolution.

---

## Phase 4 — canonical premium views

Choose a small subset of `SHOWCASE_SCENARIOS.md` and add the missing explicit view semantics needed for presentation.

Recommended first set:

1. electrostatic field laboratory;
2. Maxwell wave;
3. quantum probability/phase;
4. thermoelastic solid;
5. Schwarzschild geodesics.

Do not start with all scientific domains.

### Exit criteria

Each scenario produces a complete renderer-neutral Scene/presentation plan without Blender-specific scientific code.

---

## Phase 5 — Blender premium presentation adapter

Implement Blender interpretation from `BLENDER_PREMIUM_PRESENTATION.md`.

Initial focus:

- theme/world;
- camera;
- scientific studio lights;
- quantitative surface colors;
- legend/text mapping;
- deterministic ownership/cleanup.

Preserve existing incremental backend behavior.

### Do not initially require

- complex compositor stack;
- every Geometry Nodes optimization;
- volumetric rendering;
- advanced screen-space UI overlays.

### Exit criteria

- canonical scenarios visually coherent;
- object/datablock stability preserved during animation;
- cleanup returns owned state to baseline;
- switching presets does not rebuild unrelated scientific geometry;
- no renderer code leaks into domains/Core.

---

## Phase 6 — Geometry Nodes / dense premium rendering

Only after basic premium Blender mapping is correct.

Targets:

- PointCloud instancing;
- VectorGlyphSet arrow instancing;
- per-instance color/scale attributes;
- large-field display LOD;
- stable incremental attribute updates.

### Exit criteria

- dense premium representation remains batched;
- performance improves over per-spline/mesh fallback where relevant;
- no object-count scaling with data-point count.

---

## Phase 7 — public SDK facade

Implement a conservative `spectra.sdk` facade from `PUBLIC_SDK_FACADE.md`.

Do this after the domain/numerical/presentation contracts have settled enough that the facade is not immediately churned.

Initial SDK should expose only highly stable infrastructure.

### Exit criteria

- plain-Python import works without Blender/GPU;
- documented extension example imports only `spectra.sdk` plus subject public APIs;
- SDK export tests exist.

---

## Phase 8 — plugin descriptor and explicit external discovery

Implement plugin packaging only after the SDK facade exists.

Initial scope:

- in-process `PluginDescriptor`;
- explicit list of plugin descriptors/factories;
- compatibility validation;
- deterministic integration into active catalog;
- enable/disable state.

Add Python entry-point discovery only after this in-process model is tested.

### Exit criteria

- third-party test package can add a domain without editing Core/built-in manifest;
- registration remains transactional;
- conflict diagnostics deterministic;
- plain engine works with plugin disabled/uninstalled.

---

## Phase 9 — project document envelope

Implement the smallest useful `spectra.project` schema from `PROJECT_DOCUMENT_MODEL.md`.

Initial scope:

- project metadata;
- model records;
- presentation variant references;
- experiment artifact references;
- environment requirements.

Do not solve large numerical data storage in the first schema version.

### Exit criteria

- project round-trip serialization;
- schema/version validation;
- one scientific project can produce multiple presentation variants;
- project is independent from `.blend`.

---

## Phase 10 — native CPU numerical provider

Once the current solver-role architecture is green and presentation/project work has a clean checkpoint, implement the first high-performance provider from `HIGH_PERFORMANCE_ROADMAP.md`.

Recommended first target:

```text
ode.first_order / rk4.native_cpu
```

Why first:

- simple parity target;
- affects many higher-level domains through role dispatch;
- proves provider ABI/buffer boundary;
- does not require GPU availability.

### Exit criteria

- reference parity;
- convergence order preserved;
- provenance reports native implementation/backend;
- role policy can select it;
- high-level PDE/mechanics domains run without code changes.

---

## Phase 11 — typed numerical buffers

Promote the execution-buffer contract into runtime only after the first native provider proves which abstractions are actually needed.

Avoid prematurely forcing all Python reference semantics through a heavy buffer object.

Initial targets:

- contiguous scalar state;
- vector state;
- uniform-grid scalar field;
- host/device ownership metadata later.

---

## Phase 12 — GPU numerical provider

Only after native CPU/provider/buffer contracts are proven.

First GPU targets should favor highly parallel, clear workloads:

- batched ODE cases;
- grid Laplacian/gradient/divergence;
- simple diffusion/transport kernels.

Do not start with the most complicated multiphysics solver.

### Exit criteria

- numerical parity first;
- transfer costs measured separately;
- device-resident batching demonstrated;
- solver policy can prefer/fallback GPU cleanly;
- scientific domains remain unchanged.

---

## Phase 13 — standalone/WebGPU product surface

Only after project/presentation/Scene contracts are sufficiently stable.

A WebGPU product should consume the same project/result/presentation semantics rather than becoming a second scientific engine.

---

## Parallel work allowed between phases

Some work can safely happen in parallel if it does not mutate the same foundational contracts:

- documentation/examples;
- canonical scenario definitions;
- visual design references;
- benchmark datasets;
- scientific reference cases;
- UI wireframes;
- plugin sample package skeletons;
- native provider build research.

Avoid parallel incompatible edits to:

- DomainRegistry;
- numerical solver dispatch;
- presentation core types;
- project schema;
- Scene schema.

## Checkpoint discipline

After each foundational phase, create a new verified local baseline before stacking another major cross-cutting refactor.

Recommended sequence:

```text
foundation change
    -> targeted tests
    -> full pytest
    -> native Blender smoke if Scene/backend changed
    -> record commit/count
    -> continue
```

This prevents another 100-commit unvalidated foundation stack unless there is a deliberate reason.

## Priority recommendation

After the current numerical batch is green, the highest-value product sequence is:

```text
Presentation semantics
    -> Presentation composer
    -> Quantitative colors/legends
    -> 5 canonical premium scenes
    -> Blender premium adapter
```

Then:

```text
Public SDK
    -> plugin discovery
    -> project document
```

Native CPU/GPU execution can proceed as a separate performance track once solver contracts are validated.

## Success criterion

Each phase should prove one abstraction while keeping existing scientific domains stable.

The project should become more capable without returning to a monolithic model where science, rendering, UI, plugins, and GPU execution must change together.
