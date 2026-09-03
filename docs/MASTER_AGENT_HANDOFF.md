# Spectra Science — Master Agent Handoff

Status: **single consolidated execution brief for the next local agent pass**.

This is the primary handoff for the next large implementation/validation task. It intentionally consolidates the current runtime status, fixed architecture decisions, implementation-ready documents, validation order, and final report requirements so the agent does not need to reconstruct the plan from dozens of notes.

## Mission

Take current `main`, qualify the implemented-but-not-yet-fully-validated numerical/experiments runtime batch, fix any root regressions, then implement the next coherent platform milestone as one large local work session:

```text
G0  validate pending numerical/experiments runtime
P   Premium Presentation Phase 1
A   generic visual attributes + Scene v5
B   Blender premium/incremental realization
S   curated SDK + plugin runtime + semantic metadata core
J   project v1 runtime/document foundation
N   first native CPU ODE provider contract proof
```

The agent may make multiple logical commits locally while working, but the user wants this handled as **one consolidated patch/task** rather than repeatedly handing tiny prompts back and forth. Do not stop after each small work package merely to ask for confirmation. Validate internally at sensible boundaries and continue unless a genuine blocker exists.

Do **not** create GitHub Actions.

Do **not** implement a real GPU provider in this consolidated patch. GPU provider architecture is documented, but promotion requires a separate GPU-available validation pass. Native CPU is sufficient to prove solver replacement boundaries here.

## Runtime truth before this task

### Last fully verified runtime baseline

```text
acb9e056326177fac49cc57b202ca80cca5090a7
```

Reported at that milestone:

```text
compileall: PASS
pytest: 224 passed
initial failures: 0
auto-discovery/catalog: PASS
106 unique deterministic domains
403 providers
Blender 5.2 native targeted smoke: PASS
repo clean/synced
```

### Implemented runtime awaiting next validation

Executable development continued through:

```text
00b5403a9ffb005b7eb011833174e013158ee1f4
```

This batch added/changed:

- numerical solver registry/interchangeability;
- stable `ode.first_order` role;
- runtime role dispatch across ODE-backed PDE/physics/chemistry consumers;
- RK4 reference provider;
- Heun/RK2 reference provider;
- adaptive Dormand-Prince/RK45 provider;
- execution metadata;
- requirements/problem compatibility;
- ordered solver policies/fallback;
- fixed/adaptive provenance;
- requested vs accepted steps;
- dynamic method-of-lines provenance;
- parameter sweeps/batching;
- solver comparisons;
- convergence;
- sensitivity;
- deterministic uncertainty;
- calibration;
- Pareto/ranking;
- reproducibility fingerprints;
- experiment JSON artifacts;
- per-case numerical execution tracing.

### Runtime freeze after `00b5403...`

After that executable checkpoint, architecture/source-audit work intentionally changed only:

```text
README.md
docs/*
```

Do not mistake design documents for implemented runtime features.

## Fixed architecture decisions

These decisions are already source-audited. Do not reopen them casually during implementation.

### Scientific architecture

```text
scientific semantics
    -> reusable capabilities
    -> numerical execution roles
    -> semantic results
    -> VisualizationRegistry/base Scene
    -> presentation enrichment
    -> backend
```

Blender/WebGPU/native backends do not own scientific formulas.

### Visualization vs presentation

`VisualizationRegistry` remains:

```text
semantic object -> scientifically meaningful base Scene
```

Premium presentation remains:

```text
base Scene + PresentationIntent -> presentation-enriched Scene
```

Do not create separate cinematic/publication scientific compilers.

### Presentation coordinate space

Presentation camera framing must use:

```text
scene_local_bounds(...)
```

not world/parent-mapped `scene_bounds(...)`, because Scene camera transforms are Scene-local and the backend applies `Scene.frame` at the root.

### Timeline ownership

Current `Timeline` rejects duplicate `(target_id, property_path)` tracks.

Scientific animation owns existing scientific tracks. Presentation must not silently override them.

For first implementation:

```text
scientific track conflict -> skip presentation track + diagnostic
```

Do not invent generic animation blending in this patch.

### Backend capability source of truth

`spectra.backends.base.BackendCapabilities` already exists.

Extend it additively when required. Do not introduce parallel `RendererCapabilities`/`PresentationBackendCapabilities` sources of truth.

### Backend lifecycle

Product/project code should use:

```text
BackendSession.open(...)
BackendSession.seek(...)
BackendSession.close()
```

and not manage Blender-native handles as scientific/product state.

### Solver source of truth

`NumericalSolverRegistry` and `DomainRegistry.register_numerical_solver(...)` already provide the execution-selection foundation.

Do not create another solver/plugin registry for native CPU.

### Project provenance

Reuse existing:

```text
ScientificEnvironmentSnapshot
SolverPolicyRecord
NumericalRunArtifact
ExperimentArtifact
```

Project state stores user **selection intent** separately, conceptually `ProjectSolverSelection`.

Do not duplicate execution provenance formats in the project layer.

### Plugin catalog composition

Plugins contribute normal domain factories.

Build the active scientific catalog from:

```text
BUILTIN_DOMAIN_FACTORIES + enabled plugin domain factories
    -> DomainCatalog.from_factories(...)
```

Probe first; activate only on successful catalog construction.

First plugin runtime does not need hot-unload from a mutated live DomainRegistry. Disable/removal may take effect in a fresh runtime/catalog.

### Scene v5 reason

Current Scene schema v4 has no generic named visual attribute channel for continuous Surface scalar fields.

Scene v5 is justified specifically for generic visual attributes, not for unrelated presentation convenience.

Do not smuggle background/world/compositor settings into the same schema patch unless clearly required and independently justified.

## G0 — Validate the pending numerical/experiments runtime

Start from current local repo state.

### Repository hygiene

Run:

```text
git status --short --branch
git rev-parse HEAD
git log -1 --oneline --decorate
git pull
```

Do not overwrite unrelated local user changes. If local changes exist, inspect and preserve them.

### Baseline validation

Run using the correct local Python/venv:

```text
python -m compileall spectra
pytest -q
```

Initial expected historical baseline was 224 tests, but current suite should be higher. Report actual count; do not hardcode a target count.

### Explicit catalog probe

Construct `builtin_domain_catalog()` and verify:

- no import/constructor failure;
- no duplicate domain names;
- no ambiguous providers;
- dependency closure resolves;
- discovered names deterministic/sorted where contract requires it;
- current domain/provider counts recorded.

### Focus areas

Explicitly validate the post-baseline numerical/experiments features, including:

```text
solver interchangeability
solver policies
RK4 / Heun / RK45
problem compatibility
fixed/adaptive provenance
requested/accepted steps
method-of-lines provenance
parameter sweep
batching
solver comparison
convergence
sensitivity
uncertainty
calibration
Pareto/ranking
reproducibility snapshots
active policy fingerprinting
experiment artifacts
per-case/multi-run tracing
auto-discovery/catalog
```

If a failure occurs:

- fix production root cause first;
- change a test only when the expected contract is genuinely stale/wrong;
- do not weaken a test merely to regain green;
- rerun focused tests, then full suite.

Only continue into new executable architecture when G0 is green.

## P — Premium Presentation Phase 1

Primary references:

```text
PRESENTATION_API_DRAFT.md
PRESENTATION_PRESET_DEFAULTS.md
PRESENTATION_COMPOSER_PIPELINE.md
PRESENTATION_TEST_FIXTURES.md
PRESENTATION_RESOURCE_NAMESPACE.md
PRESENTATION_RESOURCE_ALGORITHMS.md
ANIMATION_COMPOSITION_CONTRACT.md
CAMERA_FIT_ALGORITHMS.md
SCIENTIFIC_COLOR_POLICY.md
PHASE1_PRESENTATION_IMPLEMENTATION_CHECKLIST.md
```

### P1 — value contracts and preset resolver

Implement renderer-neutral immutable presentation value types and deterministic preset resolution.

Suggested concepts:

```text
PresentationPreset
CameraMode
AnnotationDensity
LightingMode
ColorScalePolicy
CameraPolicy
LegendPolicy
AxesPolicy
AnnotationPolicy
LightingPolicy
AnimationPolicy
QualityPolicy
PresentationIntent
ResolvedPresentation
resolve_presentation(...)
```

Keep backward compatibility for existing `spectra.presentation` helpers.

Do not change Scene schema here.

### P2 — deterministic camera

Implement Scene-local fit camera using:

```text
scene_local_bounds
Transform3D.look_at
Camera
```

Requirements:

- deterministic direction/up fallback;
- perspective/orthographic support;
- robust empty/degenerate bounds handling;
- deterministic ID `presentation.camera.primary`;
- preserve/replace existing active camera according to policy;
- non-default `CoordinateFrame3D` fixture must pass.

### P3 — composer skeleton

Implement conceptually:

```python
compose_presentation(scene, intent, context=None) -> Scene
```

Use the pass order in `PRESENTATION_COMPOSER_PIPELINE.md`.

First passes:

```text
resolve policy
reconcile previous presentation-owned resources
capture scientific content set
compute scientific local bounds
camera
basic lights
basic titles/annotations
basic axes
presentation animation
final Scene validation
```

Input Scene remains immutable.

Scientific primitive IDs remain stable.

Recomposition must be deterministic/idempotent.

### P4 — basic lights/labels/axes

Use existing generic primitives only:

```text
Light
TextLabel
Polyline
Group
```

Do not add a Core `Axes` primitive in this patch.

Use deterministic presentation IDs.

### P5 — animation composition

Reuse/refactor current:

```text
merge_timelines
staggered_reveal
```

Pre-detect duplicate scientific track ownership and skip conflicting presentation tracks with structured diagnostics.

No generic track blending.

### P6 — Phase 1 generic gate

Run all relevant `PRESENTATION_TEST_FIXTURES.md` cases through plain Python plus MemoryBackend/BackendSession where useful.

Required properties:

- input Scene unchanged;
- scientific IDs unchanged;
- presentation IDs deterministic;
- repeated composition stable;
- Scene-local camera correct;
- timeline conflicts handled explicitly;
- no Blender import in generic presentation modules;
- full pytest green.

## A — Generic visual attributes and Scene v5

Primary references:

```text
VISUAL_ATTRIBUTE_MODEL.md
VISUAL_ATTRIBUTE_API_DRAFT.md
SCENE_SCHEMA_EVOLUTION_CHECKLIST.md
SCENE_V5_VISUAL_ATTRIBUTE_MIGRATION_PLAN.md
COLOR_SCALE_ALGORITHMS.md
BACKEND_CAPABILITIES_EXTENSION_PLAN.md
```

### A1 — immutable visual attribute model

Implement a minimal generic attribute contract supporting initial associations:

```text
vertex
instance
primitive
```

Initial value kinds:

```text
scalar
vec2
vec3
color
```

Requirements:

- explicit name/id;
- association;
- value kind;
- immutable values;
- strict length/shape validation;
- optional quantity/unit semantics using existing `Dimension`/`Unit` types;
- no renderer shader dictionaries;
- no arbitrary Python objects.

### A2 — attach attributes to relevant primitives

Prefer a small generic reusable attribute container rather than subject-specific `temperature_values`, `stress_values`, etc.

Immediate target is faithful continuous Surface scalar fields while retaining compatibility for PointCloud/VectorGlyphSet.

Do not force every primitive type to support every association.

### A3 — Scene v5 serialization

Bump writer intentionally to Scene v5 if the schema changes.

Requirements:

- v1-v4 reader compatibility retained;
- v4 files without attributes read unchanged;
- v5 attributes round-trip;
- malformed lengths/kinds fail clearly;
- deterministic JSON ordering remains;
- historical fixtures stay readable;
- no silent destructive downgrade.

### A4 — capability extension

Extend existing `BackendCapabilities` additively for attribute support where needed.

Old backends/tests should retain existing defaults.

Compatibility diagnostics must distinguish optional presentation degradation from scientific inability to represent required data.

## B — Blender Premium realization

Primary references:

```text
BLENDER_PREMIUM_IMPLEMENTATION_BLUEPRINT.md
BLENDER_PREMIUM_PRESENTATION.md
BLENDER_PREMIUM_SOURCE_AUDIT.md
BLENDER_PREMIUM_ACCEPTANCE.md
BACKEND_SESSION_PRODUCT_CONTRACT.md
```

Current backend layout:

```text
spectra/backends/blender/backend.py
spectra/backends/blender/incremental.py
spectra/backends/blender/timeline.py
```

Do not create a second Blender backend/presentation engine.

### B1 — composed Scene smoke

Feed Phase 1 presented Scenes through current `IncrementalBlenderBackend`.

Validate:

- camera;
- lights;
- labels;
- axes/context primitives;
- scientific geometry;
- active camera;
- cleanup.

### B2 — incremental presentation resources

Add targeted in-place paths where justified for camera/light/text changes.

Requirements:

- same semantic ID -> same Blender object/datablock where structure compatible;
- camera-only/presentation-only update does not rebuild scientific geometry;
- object/material counts remain stable.

### B3 — material lifecycle

Prevent material accumulation across apply/preset switching.

Preserve user/unrelated materials.

Do not delete based solely on names.

### B4 — generic visual attributes

Implement faithful Blender realization for the new generic attributes.

Do not use one native material per scalar sample.

Prefer mesh/instance attributes + bounded material/node representation.

For continuous scalar Surface data, a generic attribute -> color-ramp material/Geometry Nodes path is expected.

The engine remains authoritative for scalar values, scale/range, units, and palette semantics.

### B5 — dense instancing/Geometry Nodes where justified

Use only when it clearly improves PointCloud/VectorGlyphSet dense representation without changing scientific semantics.

Keep a fallback path for backends/versions that do not support the premium representation.

### B6 — Blender native gate

At minimum use Blender 5.2 targeted smoke for:

- presentation camera/light/text;
- one scalar Surface attribute/colorbar case;
- one PointCloud/VectorGlyphSet quantitative case;
- repeated preset composition/apply;
- identity stability;
- count/leak stability;
- cleanup safety.

Full old 10k/121-frame benchmark need not be repeated unless backend fast paths changed materially enough to justify it. If they do change materially, rerun the relevant stress benchmark.

## S — Curated SDK, plugin runtime, semantic metadata

Primary references:

```text
PUBLIC_SDK_FACADE.md
SDK_EXPORT_MATRIX.md
MODULE_SDK.md
PLUGIN_RUNTIME_API_DRAFT.md
PLUGIN_SDK_QUICKSTART.md
SAMPLE_EXTENSION_PACKAGE.md
METADATA_RUNTIME_API_DRAFT.md
SEMANTIC_METADATA_FIELD_CATALOG.md
INTROSPECTION_API_DRAFT.md
```

### S1 — curated `spectra.sdk`

Create a small stable facade without bloating root `spectra`.

Prefer grouped modules, conceptually:

```text
spectra.sdk.scene
spectra.sdk.domain
spectra.sdk.numerics
spectra.sdk.experiments
spectra.sdk.units
spectra.sdk.visualization
```

Re-export existing runtime classes/functions rather than cloning them.

### S2 — metadata registry

Implement optional/transactional semantic metadata infrastructure.

Do not make metadata mandatory on every existing `DomainModule` immediately.

Live provider/version authority remains `DomainRegistry`/`DomainCatalog`.

Metadata should add human/machine descriptions, parameter/unit constraints, view metadata, etc., not duplicate capability ownership.

### S3 — plugin runtime

Implement conservative in-process:

```text
PluginDescriptor
PluginRequirement
PluginRegistry
PluginState/status/diagnostics
catalog_with_plugins(...)
```

First version:

- explicit descriptors supplied by application code;
- deterministic enable/disable state;
- plugin dependency validation;
- build active catalog from factory union;
- duplicate domain/capability conflicts fail before activation;
- project files never auto-install/enable code;
- no native-library auto-loading;
- no hot-unload requirement from already-mutated live registry.

Use the documented optics sample as the acceptance proof.

## J — Project v1 foundation

Primary references:

```text
PROJECT_DOCUMENT_MODEL.md
PROJECT_RUNTIME_API_DRAFT.md
PROJECT_V1_CANONICAL_EXAMPLES.md
PROJECT_STATE_MODEL.md
SCHEMA_VERSIONING_POLICY.md
CACHE_AND_ARTIFACT_STORAGE.md
```

Implement a deliberately small project v1.

### J1 — immutable project document

Initial concepts:

```text
ProjectMetadata
ModelRecord
ProjectSolverSelection
ResultRecord
ViewRecord
PresentationVariantRecord
EnvironmentRequirement
ProjectDocument
```

Do not inline giant numerical histories in project JSON.

Do not serialize arbitrary callables/dataclasses automatically.

### J2 — deterministic serializer

Provide deterministic dict/JSON round-trip.

Requirements:

- explicit schema/version;
- duplicate IDs rejected;
- invalid references rejected;
- malformed/unknown schema does not execute code;
- project plugin requirements are declarative only.

### J3 — minimal runtime facade

Implement only enough to:

- load/validate document;
- inspect environment requirements;
- track invalidation/staleness;
- attach result references;
- compile a view using existing visualization contracts;
- apply presentation via the new composer;
- leave Blender handles/cache out of scientific project source-of-truth.

Reuse existing reproducibility and experiment artifacts.

## N — First native CPU ODE provider

Primary references:

```text
NATIVE_CPU_IMPLEMENTATION_BLUEPRINT.md
NATIVE_PROVIDER_API_DRAFT.md
NATIVE_NUMERICAL_BACKENDS.md
NUMERICAL_BUFFERS.md
NUMERICAL_BACKEND_VALIDATION.md
CANONICAL_REFERENCE_CASES.md
```

### N1 — separate optional provider

Prefer a removable provider package rather than embedding native implementation into scientific domains.

Target registration:

```text
role: ode.first_order
implementation: rk4.native_cpu
```

Current semantic contract remains:

```text
FirstOrderSystem -> ODESolution
```

### N2 — native contract proof

Implement native fixed-step RK4 with float64 execution metadata.

A CPython C extension is a good first proof if local build tooling supports it. A clean C ABI/ctypes bridge is acceptable if simpler locally.

Do not begin with CUDA/Rust/CMake-heavy infrastructure.

### N3 — parity and dispatch

Validate:

- native/reference parity on canonical ODEs;
- expected RK4 convergence;
- solver registry selection;
- explicit implementation selection;
- problem compatibility;
- tracked provenance says `kind=cpu` and `rk4.native_cpu`;
- one high-level PDE/physics consumer dispatches through the role without source changes.

Performance measurement is useful, but first checkpoint is contract correctness. Python derivative callbacks may dominate and should be reported honestly.

## Consolidated quality requirements

Throughout the task:

### Architecture

- no `bpy` imports in scientific/core/domain computation modules;
- no solver formulas inside renderer backends;
- no renderer-native objects in project scientific state;
- no duplicate capability/provider registries;
- no duplicate execution provenance formats;
- no subject-specific fields smuggled into generic Core when a generic attribute contract exists;
- no silent scientific downsampling/reinterpretation in presentation.

### API/backward compatibility

- existing public imports remain where feasible;
- current `staggered_reveal` behavior retained or cleanly superseded with compatibility;
- Scene v1-v4 remains readable after v5;
- reference RK4 capability remains available;
- existing solver role consumers continue working with default reference behavior when native provider absent;
- Blender remains optional/import-safe outside Blender.

### Diagnostics

Use structured diagnostic categories/codes from:

```text
DIAGNOSTICS_AND_ERRORS.md
DIAGNOSTIC_CODE_MATRIX.md
```

Do not collapse every failure to generic `ValueError` where subsystem context is known, but avoid a massive exception hierarchy refactor unless necessary.

### Security/trust

- parsing Scene/project/artifact JSON executes no arbitrary code;
- project requirement inspection does not install/enable plugins;
- third-party/native plugins are executable trust boundaries;
- keep restricted expression safety intact.

## Validation strategy during the consolidated task

Although this is one large user-facing task, validate internally at boundaries so a late failure is attributable.

Recommended internal checkpoints:

```text
G0 full green
P6 full plain Python green
A Scene v5/attribute full green
B Blender targeted native green
S SDK/plugin/metadata full green
J project v1 full green
N native CPU provider parity/dispatch green
FINAL full suite + catalog + selected native smoke
```

Do not ask the user for confirmation between these checkpoints unless a genuine external blocker prevents progress.

## Final validation

At the end, run:

```text
python -m compileall spectra
pytest -q
```

plus explicit:

- `builtin_domain_catalog()` probe;
- auto-discovery counts;
- solver inventory/default/policy checks;
- presentation fixture suite;
- Scene v4 historical read + v5 attribute round-trip;
- plugin optics acceptance path;
- project v1 canonical examples/round-trip;
- native CPU provider parity/dispatch if built in this environment;
- Blender 5.2 targeted premium smoke if Blender is available.

If a native compiler or Blender executable is unavailable, do not fake PASS. Report the blocked subgate precisely and still complete all testable work.

## Git discipline

- preserve user local changes;
- no GitHub Actions;
- do not commit temporary smoke scripts/artifacts;
- logical local commits are fine;
- only push final work when the applicable suite is green or the remaining blocker is external and explicitly documented;
- final repo status should be clean.

## Final report

Report compactly but completely:

```text
final SHA
compileall PASS/FAIL
full pytest PASS/FAIL + actual count
initial G0 failure count
final domain count
final provider count
solver role/RK45/provenance status
Premium Presentation status
Scene v5/visual attributes status
Blender premium smoke status
SDK/plugin/metadata status
project v1 status
native CPU provider status/parity/performance note
root fixes made
new tests added
backward compatibility notes
external blockers remaining
repo clean/sync status
```

## Deliberately out of scope for this consolidated patch

Do not let these derail the milestone:

```text
real CUDA/GPU solver provider
industrial CFD/FEA/FDTD solver replacement
full volumetric renderer
standalone/WebGPU product UI
remote/HPC worker runtime
collaboration server
plugin marketplace/install system
advanced screen-space UI layout engine
production report designer
```

Their architecture remains documented and can follow after this milestone validates the core extension/product boundaries.

## Success criterion

After this consolidated task, Spectra should have:

1. a newly re-verified numerical/experiments foundation;
2. a real renderer-neutral Premium Presentation runtime;
3. generic scientific visual attributes with backward-compatible Scene v5 persistence;
4. Blender realization of the premium/quantitative Scene without moving science into Blender;
5. a curated extension SDK and conservative plugin path;
6. a minimal persistent project/study envelope;
7. a real second execution class (`native CPU`) proving scientific domains can switch execution providers without rewrite;
8. full status/test evidence tying these claims to one final SHA.
