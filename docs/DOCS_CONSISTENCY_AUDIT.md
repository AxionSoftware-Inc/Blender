# Spectra Science — Documentation Consistency Audit

Status: **final targeted architecture/status audit before the consolidated agent patch**.

This audit records cross-document decisions checked against executable source. It is not a substitute for runtime tests.

For the next implementation task, `MASTER_AGENT_HANDOFF.md` is the primary execution brief and `FINAL_GAP_CLOSURE.md` records why no material design blocker remains.

## Runtime status invariant

```text
VERIFIED
  acb9e056...
  224 passed
  DomainCatalog/auto-discovery PASS
  Blender 5.2 targeted native validation PASS

IMPLEMENTED / VALIDATION PENDING
  acb9e056... -> 00b5403...
  solver roles / RK45 / experiments / provenance / artifacts

DESIGN / DOCS ONLY AFTER RUNTIME FREEZE
  premium presentation / visual attributes / SDK / plugins /
  project / native CPU-GPU design / product architecture
```

No design document should be reported as implemented runtime functionality before the next consolidated patch validates it.

## Decision 1 — one scientific registry model

Executable source confirms:

```text
DomainRegistry
DomainCatalog
DomainModule
```

remain the scientific domain/capability runtime.

Plugins contribute normal domain factories. Native solver providers register through normal `DomainRegistry.register_numerical_solver(...)`.

Do not create parallel plugin/native/presentation scientific registries.

## Decision 2 — one solver-role runtime

Current runtime owns:

```text
NumericalSolverRegistry
NumericalSolverImplementation
NumericalExecutionDescriptor
NumericalSolverRequirements
NumericalSolverPolicy
```

Native CPU/GPU providers extend this model. First native CPU target remains:

```text
ode.first_order / rk4.native_cpu
```

alongside `rk4.reference`.

## Decision 3 — visualization and presentation stay separate

Executable `VisualizationRegistry` remains:

```text
semantic value -> base Scene
```

Presentation owns camera, lighting, legends, axes, annotations, reveal, and visual styling:

```text
base Scene + PresentationIntent -> enriched Scene
```

Do not add renderer/preset-specific scientific compilers.

## Decision 4 — backend remains Scene consumer

Generic lifecycle remains:

```text
Backend.create(static Scene)
Backend.apply(handle, static Scene)
Backend.destroy(handle)
```

`BackendSession` owns timeline sampling/seek orchestration.

Blender/WebGPU do not solve or semantically compile scientific problems.

## Decision 5 — `BackendCapabilities` is the only capability source of truth

Prior parallel `RendererCapabilities` / `PresentationBackendCapabilities` ideas are rejected.

Premium/attribute support extends existing `BackendCapabilities` additively with conservative defaults.

## Decision 6 — presentation camera uses Scene-local bounds

Because `Scene.frame` becomes the backend root/world transform while camera/primitive transforms remain local under it, auto-camera uses:

```text
scene_local_bounds(...)
```

not frame-applied `scene_bounds(...)`.

This is fixed in camera algorithms, composer pipeline, feasibility audit, and test fixtures.

## Decision 7 — scientific animation owns conflicting properties

Current `Timeline` rejects duplicate:

```text
(target_id, property_path)
```

First presentation contract:

```text
scientific ownership wins
presentation conflict -> skip + diagnostic
```

Generic track blending is deliberately out of scope for the consolidated milestone.

## Decision 8 — Presentation Phase 1 does not require Scene schema change

Current Scene format is v4 and reads v1-v4.

Camera/lights/labels/basic axes/reveal use existing primitives/resources.

Scene v5 is reserved for the separately justified generic visual-attribute contract.

## Decision 9 — visual attributes are generic visualization data

Current source limitation:

- `Surface` has one primitive color;
- PointCloud/VectorGlyphSet have color tuples but no named generic scalar channels;
- Blender high-cardinality material-slot colors are not a final continuous-field solution;
- no generic attribute-only incremental update path exists.

The chosen direction is a generic immutable visual-attribute model, initially:

```text
associations: vertex / instance / primitive
kinds: scalar / vec2 / vec3 / color
```

Exact Python dataclass field placement may be finalized while implementing Scene v5 fixtures, but the architectural meaning is fixed and renderer-neutral.

## Decision 10 — Scene v5 migration boundary is fixed

Scene v5 is for persisted visual attributes.

Required behavior:

- v1-v4 read compatibility retained;
- v4 attribute absence maps cleanly to default/empty attributes;
- v5 attribute round-trip;
- strict validation of association/kind/value count;
- no silent destructive downgrade;
- unrelated world/background/compositor schema is not bundled merely because version changes.

## Decision 11 — project selection intent differs from execution provenance

Executable runtime already owns:

```text
ScientificEnvironmentSnapshot
SolverPolicyRecord
ExperimentArtifact
NumericalRunArtifact
```

Project docs therefore use a separate user-intent concept (`ProjectSolverSelection`) and reuse existing execution/result provenance.

No duplicate project solver/environment artifact family.

## Decision 12 — plugin activation uses candidate catalog construction

`DomainCatalog.from_factories()` already probe-loads domains and derives provider ownership from real `provide()` calls.

Plugin activation therefore follows:

```text
built-in factories + enabled plugin factories
    -> candidate DomainCatalog.from_factories(...)
    -> validate
    -> activate candidate
```

Plugin v1 does not require hot-unloading already-loaded domain objects from a mutated live registry.

Python package entry-point auto-discovery remains a later adapter over the explicit in-process descriptor model and is not required for this consolidated patch.

## Decision 13 — root `spectra` remains small

Future extension-facing imports live in curated `spectra.sdk.*` facade modules that re-export existing authoritative objects.

Do not export hundreds of classes from root `spectra.__init__`.

## Decision 14 — semantic metadata is additive

Metadata/introspection supplements, but does not replace:

```text
semantic constructor validation
DomainRegistry provider/version truth
NumericalSolverRegistry method/execution metadata
VisualizationRegistry compiler registrations
```

Metadata is optional/transactional initially. No giant hand-maintained central metadata manifest.

## Decision 15 — native CPU proof comes before real GPU implementation

The first native provider proves:

```text
provider packaging
semantic adapter
role registration
selection/policy
provenance
reference parity
high-level dispatch without domain rewrite
```

The documented preferred first target is `rk4.native_cpu`, float64.

CPython C extension vs a clean C ABI/ctypes bridge is an implementation/toolchain choice, not an unresolved engine architecture question.

Real CUDA/GPU provider implementation is deliberately outside the consolidated patch.

## Decision 16 — premium Blender extends the existing backend

Current Blender backend already owns static mapping, incremental updates, and timeline transport.

Premium work extends:

```text
spectra/backends/blender/backend.py
spectra/backends/blender/incremental.py
spectra/backends/blender/timeline.py
```

and may extract private helpers if useful.

Do not create a second premium scientific Blender backend.

## Decision 17 — display quality remains separate from numerical quality

Presentation may change:

```text
glyph density/LOD
render samples
lighting
camera
post effects
```

It must not silently change:

```text
solver grid
step/tolerance
precision
scientific values
quantitative scale meaning
```

## Decision 18 — project files are data; plugins/native providers are executable trust boundaries

Project/Scene/artifact parsing must not execute arbitrary code.

Project requirements do not auto-install/enable plugins.

Blender/native/device pointers are never durable scientific project state.

## Decision 19 — verified measurements remain commit-scoped

Keep the recorded `acb9e056...` baseline until actual local validation establishes a new verified SHA/test count/domain-provider count/native status.

Architecture/source review alone never upgrades validation status.

## Previously listed uncertainties — current resolution

The earlier audit listed several design uncertainties. They are now classified as follows:

### Resolved sufficiently for the consolidated patch

```text
visual attribute semantics and Scene v5 migration -> VISUAL_ATTRIBUTE_API_DRAFT + migration plan
native CPU implementation direction -> NATIVE_CPU_IMPLEMENTATION_BLUEPRINT
project v1 model/examples -> PROJECT_RUNTIME_API_DRAFT + PROJECT_V1_CANONICAL_EXAMPLES
presentation camera/preset/animation behavior -> dedicated algorithms/fixtures/defaults
Blender premium path -> source audit + implementation blueprint
```

### Deliberately deferred and non-blocking

```text
renderer-neutral world/background resource
advanced screen-space legend/layout engine
generic cinematic camera-orbit animation model
volume primitive/resource semantics
real GPU buffer/provider implementation details
Python entry-point plugin auto-discovery/marketplace
```

These are not missing prerequisites for the next milestone.

## Implementation handoff hierarchy

Use documents in this order:

```text
MASTER_AGENT_HANDOFF.md          primary execution brief
FINAL_GAP_CLOSURE.md             why design phase is complete enough
POST_GREEN_TASK_BOARD.md         work-package details/gates
subsystem blueprint/fixture docs as referenced by the master handoff
```

Do not ask the next agent to reconstruct architecture from every historical document.

## Final conclusion

The documentation/source-audit phase has completed its useful job: it has converged on one domain registry, one solver system, one Scene/presentation pipeline, one backend lifecycle, one provenance family, and explicit first implementation contracts.

There is no material design blocker that warrants more speculative architecture work before the consolidated local validation/implementation pass. Remaining unknowns are executable evidence questions and should be resolved by code and tests.
