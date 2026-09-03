# Spectra Science Documentation Index

This directory records architectural contracts, validated backend behavior, current numerical design, future extension rules, and product/presentation architecture.

`README.md` at repository root gives the high-level project state. Use this index to choose the source-of-truth document for a specific subsystem.

## Start here

For a new contributor/agent, read in this order:

1. `../README.md`
2. `SYSTEM_ARCHITECTURE_MAP.md`
3. `DOMAIN_SYSTEM.md`
4. `DOMAIN_CATALOG.md`
5. `SOLVERS_AND_EXPERIMENTS.md`
6. `PREMIUM_PRESENTATION_SYSTEM.md`
7. `PRODUCT_WORKFLOWS.md`
8. `PRODUCT_MILESTONES.md`
9. `POST_VALIDATION_IMPLEMENTATION_PLAN.md`
10. the subsystem-specific documents relevant to the task.

## Platform map and policy

### `SYSTEM_ARCHITECTURE_MAP.md`

Compact map of authoring, project state, domain/capability graph, numerical execution, scientific results, visualization, presentation, renderer backends, product/export surfaces, and cross-cutting systems.

### `PRODUCT_MILESTONES.md`

Product-level milestones and exit criteria from semantic-engine foundation through numerical platform, premium presentation, SDK/plugins/project format, native/GPU/remote execution, and standalone/WebGPU product.

### `CAPABILITY_MATURITY_MODEL.md`

Shared maturity and verification vocabulary distinguishing design, prototype, reference, experimental, beta, production, targeted/full/native/stress validation, and scientific-model scope.

### `DIAGNOSTICS_AND_ERRORS.md`

Structured validation/capability/numerical/plugin/presentation/backend diagnostics, severity, solver-selection rejection reasons, failure preservation, and user-vs-developer detail rules.

### `TEST_STRATEGY_AND_CHECKPOINTS.md`

Layered validation strategy from compile/import and analytical tests through catalog, solver/provider, experiments, Scene/presentation, native Blender/GPU, stress, schema, plugin, project, CLI, and security checks; also records checkpoint discipline.

### `RELEASE_QUALIFICATION.md`

Release/subsystem qualification gates covering scientific scope, compatibility, numerical correctness, Blender/presentation, project/plugin/native/GPU/remote/data/CLI/export/security/performance, and release-report requirements.

## Engine and domain architecture

### `DOMAIN_SYSTEM.md`

Core-vs-domain boundary, capability composition, solver-role architecture, renderer independence, semantic visualization, presentation separation, experiments, plugins, and long-term modularity target.

### `DOMAIN_CATALOG.md`

Automatic built-in domain discovery, probe registration, capability ownership, dependency closure, and catalog/runtime separation.

### `SEMANTIC_METADATA_AND_INTROSPECTION.md`

Future semantic/capability/domain/view/solver metadata contracts enabling generic UI, AI authoring, docs, plugin inspection, units/constraints, and large-module introspection without hardcoded switch statements.

### `MODULE_SDK.md`

How built-in and third-party scientific modules should define semantics, dependencies, capabilities, views, numerical providers, and tests.

### `SAMPLE_EXTENSION_PACKAGE.md`

Concrete third-party package blueprint using geometric optics to demonstrate package layout, domain capabilities, units, explicit views, presentation hints, diagnostics, experiment reuse, plugin lifecycle, and testing expectations.

### `NAMING_CONVENTIONS.md`

Naming rules for domains, capabilities, solver roles/implementations, method IDs, views, presentation resources, metrics, plugins, and backend identifiers.

### `PUBLIC_SDK_FACADE.md`

Design for a curated future `spectra.sdk` import surface so external extensions do not depend on arbitrary private repository paths.

### `PLUGIN_PACKAGING.md`

Future external package/entry-point discovery model, plugin compatibility, enable/disable, provider conflicts, native plugin lifecycle, and trust boundary.

### `API_STABILITY_POLICY.md`

Public/internal API classes, capability/domain/solver identity stability, deprecation lifecycle, plugin compatibility, source-vs-data compatibility, and native ABI evolution rules.

### `SCHEMA_VERSIONING_POLICY.md`

Persistent schema identifiers, backward-read/migration rules, units/coordinates/IDs, project/Scene/experiment compatibility, plugin payloads, caches, and historical fixtures.

### `TRUST_AND_SECURITY_MODEL.md`

Trust zones for built-ins, third-party plugins, native providers, project/data files, remote resources/workers, Blender integration, expressions, secrets, and AI-generated code.

## Product and project model

### `PRODUCT_WORKFLOWS.md`

How Blender UI, standalone clients, CLI/headless workers, WebGPU, Python, and AI authoring should orchestrate the same semantic/numerical/project/presentation engine.

### `UI_INFORMATION_ARCHITECTURE.md`

Recommended product organization around Project, Model, Solve, Results, View, Presentation, Experiments, Resources, Diagnostics, and Export—without making UI/native renderer state authoritative.

### `PROJECT_STATE_MODEL.md`

Conceptual project lifecycle, dirty/invalidation states, model/result/view/presentation/renderer separation, caching, stale-result handling, local/remote execution, and product-level state transitions.

### `COMMAND_AND_UNDO_MODEL.md`

Semantic command/transaction model for UI, Python, AI, undo/redo, preview edits, solve attempts, project invalidation, renderer synchronization, and future collaboration.

### `COLLABORATION_MODEL.md`

Future semantic revision/collaboration model, merge/conflict classes, shared-vs-local state, result history, presentation variants, resource/plugin compatibility, permissions, and remote job integration.

### `PROJECT_DOCUMENT_MODEL.md`

Future renderer-independent persistent project/study envelope for scientific models, solver policies, experiment artifacts, presentation variants, Scene caches, and external data resources.

### `DATA_INGESTION_AND_RESOURCES.md`

External scientific data/resource pipeline, format adapters, units, coordinates, structured/unstructured grids, point clouds, time series, lazy/remote resources, caching, provenance, and import security.

### `HEADLESS_API_AND_CLI.md`

Headless Python/CLI orchestration for validate/solve/experiment/view/present/export/inspect/plugin/doctor workflows without requiring Blender.

### `EXPORT_AND_REPORTING.md`

Scientific data, Scene, renderer-native, image/video, report, experiment, project-archive, sidecar metadata, and provenance-aware export architecture.

### `REMOTE_EXECUTION_AND_WORKERS.md`

Remote/HPC worker contract, execution requests, capability negotiation, job lifecycle, resource staging, stale-result protection, distributed experiments, and local/remote semantic symmetry.

### `AI_AUTHORING_AND_COMPILATION.md`

AI authoring boundary: natural-language intent compiles into explicit semantic/project commands, units/capabilities/views are introspected, diagnostics remain authoritative, and AI never replaces deterministic numerical execution.

### `POST_VALIDATION_IMPLEMENTATION_PLAN.md`

Recommended implementation order after the next green validation: presentation semantics/composer, quantitative colors/legends, canonical premium scenes, Blender premium mapping, SDK/plugins/project format, then native CPU/GPU execution phases.

## Numerical execution

### `SOLVERS_AND_EXPERIMENTS.md`

Stable numerical roles, solver interchangeability, selection policies, experiments, convergence, sensitivity, uncertainty, calibration, tracing, and reproducibility.

### `NUMERICAL_PROVENANCE.md`

Current fixed/adaptive numerical method/run semantics, selected implementation/execution metadata, solver policies, PDE pipeline provenance, per-case traces, and durable artifact rules.

### `NATIVE_NUMERICAL_BACKENDS.md`

Contract for native CPU, GPU, and external solver providers.

### `NUMERICAL_BUFFERS.md`

Typed execution-buffer and data-layout design for native/GPU implementations.

### `NUMERICAL_BACKEND_VALIDATION.md`

Parity, convergence, performance, transfer, memory, and promotion criteria for high-performance numerical providers.

### `CANONICAL_REFERENCE_CASES.md`

Shared analytical/numerical/visual/performance reference cases for ODE/PDE/math/physics, experiments, native/GPU parity, Blender/WebGPU validation, and performance reporting.

### `PERFORMANCE_BUDGETS.md`

Performance workload classes, latency/throughput separation, numerical/render/project/remote budgets, memory/history/caching considerations, and benchmark reporting boundaries.

### `HIGH_PERFORMANCE_ROADMAP.md`

Incremental path from Python reference solvers to native CPU, batched execution, GPU grid operators, and device-resident pipelines.

## Presentation and rendering

### `PREMIUM_PRESENTATION_SYSTEM.md`

Renderer-neutral presentation intent: presets, camera, color scales, legends, axes, annotations, lighting, animation grammar, accessibility, quality policy, data decimation, and backend capability negotiation.

### `VISUAL_DESIGN_SYSTEM.md`

Shared product visual language for scientific hierarchy, typography roles, spacing, color semantics, geometry/material/lighting language, camera composition, multi-panel comparison, animation character, preset consistency, and accessibility.

### `PRESENTATION_RESOURCE_NAMESPACE.md`

Deterministic IDs, namespaces, ownership metadata, incremental update rules, preset switching, and cleanup behavior for cameras, lights, legends, axes, annotations, materials, and presentation tracks.

### `BLENDER_PREMIUM_PRESENTATION.md`

How Blender may realize premium presentation intent through native materials, lights, camera, attributes, Geometry Nodes, compositor, ownership, and incremental updates.

### `BLENDER_PREMIUM_ACCEPTANCE.md`

Acceptance gates for premium Blender presentation: architecture boundaries, ownership/cleanup, incremental identity, color integrity, framing, lighting, dense batching, animation, canonical scenes, preset switching, save/reload, performance, and visual review.

### `BLENDER_BACKEND.md`

Current Blender backend contract and verified Blender 5.2 native behavior.

### `SHOWCASE_SCENARIOS.md`

Canonical scientific scenes used as end-to-end integration and premium-quality targets: electrostatics, Maxwell, quantum, CFD, thermoelasticity, reaction-diffusion, geodesics, experiments, and multiphysics.

## Scientific/multiphysics notes

### `MULTIPHYSICS_3D.md`

3D field, fluid, thermal, solid, Maxwell, quantum, chemistry, and coupling architecture.

### `GEOMETRY_RELATIVITY_PDE.md`

Geometry, relativity, PDE composition and related validation notes from an earlier development milestone.

## Status hierarchy

Documents describe different kinds of truth. Interpret them carefully.

### Verified behavior

Explicit validation records such as Blender 5.2 native smoke or a stated pytest baseline describe observed behavior at a specific commit.

### Current implemented architecture

Some documents describe code already present on `main` but not yet included in the latest full local validation milestone.

### Design contract / future direction

Files such as native/GPU buffer design, premium presentation runtime phases, external plugin entry-point discovery, public SDK facade, semantic metadata, project/document/collaboration models, remote worker contract, AI authoring, and UI/headless/export architecture may describe architecture intentionally specified before implementation.

Do not report a design contract as implemented runtime functionality.

## Current validation note

The last fully reported verified baseline before the current numerical/experiment development batch was:

```text
commit: acb9e056326177fac49cc57b202ca80cca5090a7
compileall: PASS
pytest: 224 passed
Blender 5.2 LTS native smoke: PASS
```

`main` has moved beyond that baseline. The current large numerical/experiments batch should not be called fully green until its next local validation completes.

Documentation-only commits after that batch do not themselves require Blender/GPU execution validation.

## Rules for updating docs

- update architecture documents when public boundaries change;
- keep verified measurements tied to the commit/machine/context that produced them;
- distinguish implemented code from future design;
- do not write renderer-specific behavior into scientific-domain docs;
- do not document reference solvers as industrial/production CFD, FEA, FDTD, or quantum chemistry solvers;
- update this index when introducing another subsystem source-of-truth document.
