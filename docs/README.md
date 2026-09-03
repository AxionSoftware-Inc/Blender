# Spectra Science Documentation Index

This directory records architectural contracts, validated backend behavior, current numerical design, future extension rules, and product/presentation architecture.

`README.md` at repository root gives the high-level project state. `CURRENT_STATUS.md` separates verified runtime, implemented-but-pending-validation runtime, and design-only work.

## Start here

For a new contributor/agent, read in this order:

1. `../README.md`
2. `CURRENT_STATUS.md`
3. `SYSTEM_ARCHITECTURE_MAP.md`
4. `DOMAIN_SYSTEM.md`
5. `DOMAIN_CATALOG.md`
6. `SOLVERS_AND_EXPERIMENTS.md`
7. `PREMIUM_PRESENTATION_SYSTEM.md`
8. `POST_GREEN_TASK_BOARD.md`
9. `MASTER_AGENT_HANDOFF.md` when executing the next consolidated patch/validation task
10. subsystem-specific documents relevant to the work package.

## Current implementation-ready source set

These are the highest-priority documents when moving from design to executable work.

### Runtime status and execution plan

- `CURRENT_STATUS.md` — verified baseline vs pending runtime vs design-only work.
- `POST_GREEN_TASK_BOARD.md` — work-package ordering and exit gates after pending runtime validates green.
- `IMPLEMENTATION_WORK_PACKAGES.md` — larger implementation decomposition.
- `POST_VALIDATION_IMPLEMENTATION_PLAN.md` — product/performance sequencing.
- `MASTER_AGENT_HANDOFF.md` — consolidated next-agent instructions and single large task scope.
- `DOCS_CONSISTENCY_AUDIT.md` — architecture/status consistency review.
- `SOURCE_AUDIT_DECISIONS.md` — decisions derived from current executable source rather than speculative parallel abstractions.

### Premium presentation implementation

- `PRESENTATION_API_DRAFT.md`
- `PRESENTATION_PRESET_DEFAULTS.md`
- `PRESENTATION_COMPOSER_PIPELINE.md`
- `PRESENTATION_TEST_FIXTURES.md`
- `PRESENTATION_RESOURCE_NAMESPACE.md`
- `PRESENTATION_RESOURCE_ALGORITHMS.md`
- `ANIMATION_COMPOSITION_CONTRACT.md`
- `CAMERA_FIT_ALGORITHMS.md`
- `SCIENTIFIC_COLOR_POLICY.md`
- `COLOR_SCALE_ALGORITHMS.md`
- `PREMIUM_SCENE_BLUEPRINTS.md`
- `PREMIUM_SHOWCASE_ACCEPTANCE_DATA.md`
- `PHASE1_PRESENTATION_IMPLEMENTATION_CHECKLIST.md`

### Visual attributes / Scene evolution

- `VISUAL_ATTRIBUTE_MODEL.md`
- `VISUAL_ATTRIBUTE_API_DRAFT.md`
- `SCENE_SCHEMA_EVOLUTION_CHECKLIST.md`
- `SCENE_V5_VISUAL_ATTRIBUTE_MIGRATION_PLAN.md`
- `BACKEND_CAPABILITIES_EXTENSION_PLAN.md`
- `RENDERER_CAPABILITIES_API_DRAFT.md`

### Blender premium implementation

- `BLENDER_BACKEND.md`
- `BLENDER_PREMIUM_PRESENTATION.md`
- `BLENDER_PREMIUM_SOURCE_AUDIT.md`
- `BLENDER_PREMIUM_ACCEPTANCE.md`
- `BLENDER_PREMIUM_IMPLEMENTATION_BLUEPRINT.md`
- `BACKEND_SESSION_PRODUCT_CONTRACT.md`

### SDK / plugins / project runtime

- `PUBLIC_SDK_FACADE.md`
- `SDK_EXPORT_MATRIX.md`
- `MODULE_SDK.md`
- `PLUGIN_PACKAGING.md`
- `PLUGIN_RUNTIME_API_DRAFT.md`
- `PLUGIN_SDK_QUICKSTART.md`
- `SAMPLE_EXTENSION_PACKAGE.md`
- `PROJECT_DOCUMENT_MODEL.md`
- `PROJECT_RUNTIME_API_DRAFT.md`
- `PROJECT_V1_CANONICAL_EXAMPLES.md`
- `PROJECT_STATE_MODEL.md`
- `METADATA_RUNTIME_API_DRAFT.md`
- `SEMANTIC_METADATA_FIELD_CATALOG.md`
- `INTROSPECTION_API_DRAFT.md`

### Native/high-performance execution

- `NATIVE_NUMERICAL_BACKENDS.md`
- `NATIVE_PROVIDER_API_DRAFT.md`
- `NATIVE_CPU_IMPLEMENTATION_BLUEPRINT.md`
- `NUMERICAL_BUFFERS.md`
- `NUMERICAL_BACKEND_VALIDATION.md`
- `CANONICAL_REFERENCE_CASES.md`
- `HIGH_PERFORMANCE_ROADMAP.md`
- `PERFORMANCE_BUDGETS.md`
- `OBSERVABILITY_AND_PROFILING.md`

## Platform map and policy

### `SYSTEM_ARCHITECTURE_MAP.md`

Compact map of authoring, project state, domain/capability graph, numerical execution, scientific results, visualization, presentation, renderer backends, product/export surfaces, and cross-cutting systems.

### `PRODUCT_MILESTONES.md`

Product-level milestones and exit criteria from semantic-engine foundation through numerical platform, premium presentation, SDK/plugins/project format, native/GPU/remote execution, and standalone/WebGPU product.

### `CAPABILITY_MATURITY_MODEL.md`

Shared maturity and verification vocabulary distinguishing design, prototype, reference, experimental, beta, production, targeted/full/native/stress validation, and scientific-model scope.

### `DIAGNOSTICS_AND_ERRORS.md` / `DIAGNOSTIC_CODE_MATRIX.md`

Structured validation/capability/numerical/plugin/presentation/backend diagnostics and the machine-readable diagnostic code vocabulary.

### `TEST_STRATEGY_AND_CHECKPOINTS.md`

Layered validation strategy from compile/import and analytical tests through catalog, solver/provider, experiments, Scene/presentation, native Blender/GPU, stress, schema, plugin, project, CLI, and security checks.

### `RELEASE_QUALIFICATION.md`

Release/subsystem qualification gates covering scientific scope, compatibility, numerical correctness, Blender/presentation, project/plugin/native/GPU/remote/data/CLI/export/security/performance.

## Engine and domain architecture

### `DOMAIN_SYSTEM.md`

Core-vs-domain boundary, capability composition, solver-role architecture, renderer independence, semantic visualization, presentation separation, experiments, plugins, and long-term modularity target.

### `DOMAIN_CATALOG.md`

Automatic built-in domain discovery, probe registration, capability ownership, dependency closure, and catalog/runtime separation.

### `SEMANTIC_METADATA_AND_INTROSPECTION.md`

Semantic/capability/domain/view/solver metadata contracts enabling generic UI, AI authoring, docs, plugin inspection, units/constraints, and large-module introspection without hardcoded switch statements.

### `NAMING_CONVENTIONS.md`

Naming rules for domains, capabilities, solver roles/implementations, method IDs, views, presentation resources, metrics, plugins, and backend identifiers.

### `API_STABILITY_POLICY.md`

Public/internal API classes, capability/domain/solver identity stability, deprecation lifecycle, plugin compatibility, source-vs-data compatibility, and native ABI evolution rules.

### `SCHEMA_VERSIONING_POLICY.md`

Persistent schema identifiers, backward-read/migration rules, units/coordinates/IDs, project/Scene/experiment compatibility, plugin payloads, caches, and historical fixtures.

### `TRUST_AND_SECURITY_MODEL.md`

Trust zones for built-ins, third-party plugins, native providers, project/data files, remote resources/workers, Blender integration, expressions, secrets, and AI-generated code.

## Product and project model

### `PRODUCT_WORKFLOWS.md`

How Blender UI, standalone clients, CLI/headless workers, WebGPU, Python, and AI authoring orchestrate the same semantic/numerical/project/presentation engine.

### `UI_INFORMATION_ARCHITECTURE.md`

Recommended product organization around Project, Model, Solve, Results, View, Presentation, Experiments, Resources, Diagnostics, and Export.

### `COMMAND_AND_UNDO_MODEL.md`

Semantic command/transaction model for UI, Python, AI, undo/redo, preview edits, solve attempts, project invalidation, renderer synchronization, and future collaboration.

### `COLLABORATION_MODEL.md`

Future semantic revision/collaboration model, merge/conflict classes, shared-vs-local state, result history, presentation variants, resource/plugin compatibility, permissions, and remote job integration.

### `TEMPLATE_SYSTEM.md`

Versioned scientific/project/experiment/presentation/workflow templates with explicit assumptions, parameters, solver policies, views, presets, plugin integration, and AI/template-selection rules.

### `CACHE_AND_ARTIFACT_STORAGE.md`

Durable project/result/experiment artifacts versus derived scientific, Scene, presentation, renderer, resource, and execution caches.

### `DATA_INGESTION_AND_RESOURCES.md`

External scientific data/resource pipeline, format adapters, units, coordinates, structured/unstructured grids, point clouds, time series, lazy/remote resources, caching, provenance, and import security.

### `HEADLESS_API_AND_CLI.md`

Headless Python/CLI orchestration for validate/solve/experiment/view/present/export/inspect/plugin/doctor workflows without requiring Blender.

### `EXPORT_AND_REPORTING.md`

Scientific data, Scene, renderer-native, image/video, report, experiment, project-archive, sidecar metadata, and provenance-aware export architecture.

### `REMOTE_EXECUTION_AND_WORKERS.md`

Remote/HPC worker contract, execution requests, capability negotiation, job lifecycle, resource staging, stale-result protection, distributed experiments, and local/remote semantic symmetry.

### `AI_AUTHORING_AND_COMPILATION.md`

AI authoring boundary: natural-language intent compiles into explicit semantic/project commands; diagnostics and deterministic numerical execution remain authoritative.

## Numerical execution

### `SOLVERS_AND_EXPERIMENTS.md`

Stable numerical roles, solver interchangeability, selection policies, experiments, convergence, sensitivity, uncertainty, calibration, tracing, and reproducibility.

### `NUMERICAL_PROVENANCE.md`

Current fixed/adaptive numerical method/run semantics, selected implementation/execution metadata, solver policies, PDE pipeline provenance, per-case traces, and durable artifact rules.

## Presentation and rendering

### `PREMIUM_PRESENTATION_SYSTEM.md`

Renderer-neutral presentation intent: presets, camera, color scales, legends, axes, annotations, lighting, animation grammar, accessibility, quality policy, data decimation, and backend capability negotiation.

### `VISUAL_DESIGN_SYSTEM.md`

Shared product visual language for scientific hierarchy, typography roles, spacing, color semantics, geometry/material/lighting language, camera composition, multi-panel comparison, animation character, preset consistency, and accessibility.

### `VISUALIZATION_PRESENTATION_BOUNDARY.md`

Keeps semantic visualization (`semantic object -> base Scene`) separate from presentation enrichment (`base Scene -> presented Scene`).

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

Explicit validation records describe observed behavior at a specific commit.

Current recorded verified baseline:

```text
commit: acb9e056326177fac49cc57b202ca80cca5090a7
compileall: PASS
pytest: 224 passed
Blender 5.2 native smoke: PASS
```

### Implemented, awaiting validation

The executable numerical/experiments batch after the verified baseline ends at:

```text
00b5403a9ffb005b7eb011833174e013158ee1f4
```

It must not be called fully green until the next local validation completes.

### Design/documentation after runtime freeze

Changes after `00b5403...` are intentionally documentation/design/source-audit work unless `CURRENT_STATUS.md` is explicitly updated to say otherwise. These documents must not be reported as implemented runtime functionality.

## Rules for updating docs

- update architecture documents when public boundaries change;
- keep verified measurements tied to the commit/machine/context that produced them;
- distinguish implemented code from future design;
- prefer current executable source over speculative duplicate abstractions;
- do not write renderer-specific behavior into scientific-domain docs;
- do not document reference solvers as industrial/production CFD, FEA, FDTD, or quantum chemistry solvers;
- update this index when introducing another subsystem source-of-truth document.
