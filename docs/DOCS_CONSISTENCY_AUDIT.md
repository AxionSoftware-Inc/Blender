# Spectra Science — Documentation Consistency Audit

Status: **targeted architecture/status audit of the current docs-only preparation block**.

This audit records cross-document decisions that were checked against executable source so later implementation does not inherit contradictory design assumptions.

It is not a substitute for runtime tests.

## Runtime status invariant

Current status remains separated into:

```text
VERIFIED
  acb9e056...
  224 passed
  DomainCatalog/auto-discovery PASS
  Blender 5.2 native targeted validation PASS

IMPLEMENTED / VALIDATION PENDING
  acb9e056... -> 00b5403...
  solver roles / adaptive RK45 / experiments / provenance / artifacts

DESIGN / DOCS ONLY
  premium presentation / SDK / plugins / project / native GPU etc.
```

No later design document should claim Premium Presentation, ProjectRuntime, plugin manager, native CPU/GPU provider, or visual attributes are already runtime features.

## Decision 1 — one scientific registry model

Source confirms:

```text
DomainRegistry
DomainCatalog
DomainModule
```

remain the only scientific domain/capability runtime.

Therefore docs consistently reject:

```text
PluginScientificRegistry
NativeSolverDomainRegistry
PresentationDomainRegistry
```

as parallel systems.

Plugins contribute normal domain factories.

Native solver providers register through normal `DomainRegistry.register_numerical_solver(...)`.

## Decision 2 — one solver-role runtime

Source confirms current runtime owns:

```text
NumericalSolverRegistry
NumericalSolverImplementation
NumericalExecutionDescriptor
NumericalSolverRequirements
NumericalSolverPolicy
```

and `DomainRegistry` delegates to it.

Native/GPU docs therefore do not introduce a second solver selector.

First native CPU target remains:

```text
role: ode.first_order
implementation: rk4.native_cpu
```

alongside, not replacing, `rk4.reference`.

## Decision 3 — visualization vs presentation boundary

Executable `VisualizationRegistry` is type-directed:

```text
semantic value -> base Scene
```

Docs consistently place:

```text
camera
lighting
legend
axes
annotations
cinematic styling
```

in the presentation layer after semantic visualization.

Do not add `compile_cinematic_*` scientific compilers as a second semantic path.

## Decision 4 — renderer backend remains Scene consumer

Executable backend contract remains:

```text
Backend.create(static Scene)
Backend.apply(handle, static Scene)
Backend.destroy(handle)
```

`BackendSession` owns timeline sampling/seek orchestration.

Docs therefore consistently require:

```text
semantic science
 -> base Scene
 -> presentation composer
 -> Scene
 -> BackendSession/backend
```

and reject Blender-side scientific solving/semantic compilation.

## Decision 5 — existing BackendCapabilities is source of truth

Source already defines `BackendCapabilities`.

A prior design tendency toward a parallel `RendererCapabilities` / `PresentationBackendCapabilities` type was rejected.

Current design requires additive evolution of existing `BackendCapabilities`, with conservative defaults.

Capability flags describe the Spectra adapter’s implemented/validated behavior, not everything Blender/WebGPU could theoretically support.

## Decision 6 — camera uses Scene-local bounds

Source relationship:

```text
Scene.frame -> backend root/world transform
primitive/camera Transform3D -> local under that frame
```

Therefore presentation auto-camera must use:

```text
scene_local_bounds(...)
```

not frame-applied `scene_bounds(...)` for the camera’s local transform.

This rule is reflected in:

- presentation feasibility audit;
- camera algorithms;
- composer pipeline;
- test fixtures.

## Decision 7 — scientific animation owns conflicting properties

Executable `Timeline` rejects duplicate:

```text
(target_id, property_path)
```

tracks.

Therefore presentation reveal does not override or blend a scientific track by default.

Current first contract:

```text
scientific ownership wins
presentation conflicting effect skipped/diagnosed
```

Generic animation blending is intentionally deferred.

## Decision 8 — Scene v4 remains unchanged for Presentation Phase 1

Executable serializer currently uses:

```text
spectra.scene version 4
reader supports v1-v4
```

Presentation Phase 1 uses only current primitives/resources.

Do not bump Scene schema merely for:

- camera;
- lights;
- labels;
- basic axes;
- staggered reveal.

Scene v5 is reserved for a deliberate persisted contract change such as generic visual attributes/environment semantics.

## Decision 9 — visual attributes are generic visualization data

Current source evidence:

- Surface has one primitive-level color;
- PointCloud/VectorGlyphSet support color tuples but not named generic scalar channels;
- Blender current high-cardinality color path uses material slots with a guard;
- incremental geometry updates do not provide a general attribute-only update path.

Therefore quantitative Surface temperature/stress/potential etc. should gain one generic visual-attribute contract instead of domain-specific Surface subclasses or Blender-only shader recovery.

## Decision 10 — project selection intent vs execution provenance

Executable source already owns:

```text
ScientificEnvironmentSnapshot
SolverPolicyRecord
ExperimentArtifact
NumericalRunArtifact
```

Project docs therefore use a distinct concept:

```text
ProjectSolverSelection
```

for user/project execution intent.

Project runtime must reuse existing result/experiment provenance rather than invent another solver/environment artifact format.

## Decision 11 — plugin activation builds candidate catalog

Executable `DomainCatalog.from_factories()` already probe-loads domains and derives provider ownership from real `provide()` calls.

Planned plugin activation therefore uses:

```text
built-in factories
+ enabled plugin factories
 -> candidate DomainCatalog.from_factories(...)
 -> validate
 -> activate candidate
```

not in-place mutation of the currently working catalog during validation.

Hot-unloading already-loaded domain objects is not part of plugin v1.

## Decision 12 — root `spectra` remains small

Current root package deliberately exports very little.

The future public SDK is a curated facade:

```text
spectra.sdk.scene
spectra.sdk.domain
spectra.sdk.numerics
spectra.sdk.experiments
...
```

rather than exporting hundreds of classes from `spectra.__init__`.

Third-party extensions should eventually depend on curated SDK modules, not arbitrary internal paths.

## Decision 13 — native CPU proof before GPU

Architecture documents align on sequence:

```text
reference Python
 -> optional native CPU provider
 -> batch/buffer proof
 -> GPU provider
 -> GPU grid operators
 -> device-resident PDE pipeline
```

The first native provider may not be much faster when Python RHS callbacks dominate. Its first job is to prove provider/ABI/selection/provenance/parity.

No performance claim is required for architectural success.

## Decision 14 — premium Blender extends existing backend

Current Blender backend files already implement:

```text
static mapping
incremental updates
engine-time transport
```

Premium Blender plan extends these paths and may later extract backend-private helpers.

It does not create a second `PremiumBlenderScientificBackend` that bypasses current generic Scene mapping.

## Decision 15 — display quality is separate from numerical quality

Across presentation/Blender/performance docs:

```text
display glyph limit
LOD
render samples
post effects
```

may change presentation cost/quality only.

They must not silently alter:

```text
solver grid
step count/tolerance
precision
scientific field values
quantitative color range meaning
```

## Decision 16 — project files are data; plugins are executable trust boundary

Security/project/plugin docs align on:

- project JSON does not auto-install/enable plugins;
- project parse must not execute plugin payloads;
- plugin/native providers are executable code requiring application/user trust policy;
- Blender/native pointers/device pointers are never scientific project state.

## Decision 17 — verified measurements stay commit-scoped

Current docs retain `acb9e056...` as the last full reported green runtime milestone.

Do not update:

```text
pytest count
domain/provider count
native validation status
```

based on architecture/source review alone.

Only the next local validation should establish a new verified baseline.

## Targeted stale-assumption search

The audit specifically looked for old conceptual risks such as:

```text
124 passed baseline
Blender not installed/pending validation
parallel RendererCapabilities
project SolverPolicyRecord collision
hardcoded domain consumption of concrete RK4
```

No runtime status should be inferred merely from absence/presence of a text search hit; source-of-truth files above remain authoritative.

## Documentation growth rule

The docs-only preparation block is intentionally broad, but runtime implementation should no longer create new architecture documents for every small choice.

After G0 green:

- use existing contracts;
- update a source-of-truth doc only when implementation exposes a real boundary mismatch;
- prefer code/tests over another speculative layer;
- follow `POST_GREEN_TASK_BOARD.md`.

## Remaining known design uncertainties

These are intentionally not frozen yet:

1. exact persistent visual-attribute attachment shape before Scene v5;
2. whether generic environment/background becomes Scene resource or presentation/project state;
3. exact native CPU packaging mechanism/wheel strategy;
4. eventual plugin entry-point API details;
5. project v1 exact field names until implementation fixtures pass;
6. screen-space legend/annotation abstraction;
7. generic camera motion/orbit track model;
8. volume primitive/resource semantics;
9. GPU buffer API after native CPU/batch evidence.

These uncertainties are isolated and should not block Premium Presentation Phase 1.

## Implementation handoff

After pending runtime validation is green, begin with:

```text
POST_GREEN_TASK_BOARD.md
PRESENTATION_PRESET_DEFAULTS.md
PRESENTATION_TEST_FIXTURES.md
CAMERA_FIT_ALGORITHMS.md
PRESENTATION_COMPOSER_PIPELINE.md
ANIMATION_COMPOSITION_CONTRACT.md
```

Do not reread every architecture document before writing W1; the board identifies the relevant source-of-truth set.

## Success criterion

The documentation block is internally useful only if it reduces implementation ambiguity. The central architecture now has one domain registry, one solver role system, one Scene pipeline, one presentation boundary, one backend lifecycle, and one provenance family; future runtime work should implement those contracts rather than creating parallel substitutes.