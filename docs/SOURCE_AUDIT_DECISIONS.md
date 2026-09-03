# Spectra Science — Source-Audit Decisions Before Next Runtime Phase

Status: **documentation checkpoint; no runtime code changed**.

This document records concrete architecture decisions discovered by comparing future API drafts against current source. It exists so later implementation work does not reintroduce already-resolved duplicate abstractions or coordinate/lifecycle mistakes.

## 1. Presentation camera framing uses Scene-local bounds

Decision:

```text
use scene_local_bounds(scene)
```

for presentation-generated camera fitting.

Reason:

- `Camera.transform` is Scene-local;
- Blender maps `Scene.frame` onto the root object;
- using parent/world-mapped `scene_bounds()` to create a Scene-local camera risks applying the coordinate frame twice.

`scene_bounds()` remains valid for callers explicitly needing parent/world-mapped bounds.

## 2. Keep one backend capability source of truth

Current runtime already has:

```text
BackendCapabilities
```

Decision:

- extend/refine this contract for future presentation feature negotiation;
- do not introduce a parallel authoritative `RendererCapabilities` registry.

Presentation-specific fallback planning may use helper records, but backend feature truth originates from `BackendCapabilities`.

## 3. Visualization and presentation stay separate

Current `VisualizationRegistry` owns:

```text
semantic value/type -> base Scene
```

Decision:

- scientific/domain compilers produce renderer-neutral base Scenes;
- publication/cinematic/dark-lab styling is a later presentation compiler pass;
- do not register separate visualization compilers per presentation preset.

## 4. Timeline property ownership is exclusive

Current `Timeline` rejects duplicate `(target_id, property_path)` tracks.

Decision:

- scientific timeline ownership wins by default;
- presentation reveal may not silently add another `opacity` or `trim_end` track on the same target;
- conflicts must be skipped/rejected or handled by an explicit future composition operator.

## 5. Product rendering uses BackendSession lifecycle

Current generic lifecycle already exists:

```text
BackendSession.open(...)
BackendSession.seek(...)
BackendSession.close()
```

Decision:

- UI/project/CLI product layers should use this generic lifecycle;
- native Blender/WebGPU handles remain backend-private;
- scientific and presentation time remain engine-owned.

## 6. Native/GPU solvers use NumericalSolverRegistry

Current runtime already supports:

```text
solver role
implementation ID
method metadata
execution kind/backend/precision
problem compatibility predicate
priority/tags
default/policy selection
```

Decision:

- native CPU/GPU providers register ordinary `NumericalSolverImplementation`s through `DomainRegistry.register_numerical_solver()`;
- do not create a second native/GPU solver registry.

## 7. Plugin scientific domains use DomainCatalog/DomainRegistry

Current `DomainCatalog.from_factories()` probe-loads actual domain registrations and derives capability ownership.

Decision:

```text
built-in factories + enabled plugin factories
    -> new candidate DomainCatalog.from_factories(...)
    -> successful probe
    -> use candidate catalog
```

This preserves one capability/provider model and catches duplicate domains/providers before activation.

Initial plugin runtime should not attempt complex hot-unload from an already-mutated live scientific registry.

## 8. Project solver intent is not execution provenance

Existing runtime already has:

```text
ScientificEnvironmentSnapshot
SolverPolicyRecord
NumericalRunRecord / NumericalRunArtifact
ExperimentArtifact
```

Decision:

- project files store user/config selection intent as a distinct `ProjectSolverSelection`-style record;
- actual environment/run provenance reuses existing runtime artifacts;
- do not create duplicate `SolverPolicyRecord` or environment snapshot formats.

## 9. Metadata supplements live registries

Current live facts:

```text
DomainModule name/version/dependencies
DomainRegistry capabilities/provider/version
DomainCatalog provider graph
VisualizationRegistry compiler dispatch
NumericalSolverRegistry execution metadata
Dimension/Unit/Quantity
```

Decision:

- future metadata is descriptive and transactional;
- live provider/version facts remain authoritative;
- metadata should integrate into `DomainRegistry` snapshot/rollback rather than become a separate scientific runtime.

## 10. Do not force metadata into every DomainModule yet

Decision:

- keep `DomainModule` protocol unchanged initially;
- domains may optionally register metadata during normal `register()`;
- prove metadata on a few showcase types before annotating 100+ domains.

## 11. Quantitative surface visualization needs a generic attribute path

Current generic `Surface` carries one primitive-level color only.

Current batched `PointCloud`/`VectorGlyphSet` have per-instance color tuples, but Blender realizes high-cardinality colors through bounded material slots rather than a scalable attribute shader path.

Decision:

- Phase 1 premium presentation does not fake continuous scalar Surface colormaps;
- design a renderer-neutral visual-attribute buffer/channel contract as a separate checkpoint;
- later backends consume the same attribute semantics through Blender attributes/Geometry Nodes/WebGPU buffers/etc.

## 12. Animated quantitative colors need their own incremental path

Current IncrementalBlenderBackend fast paths update geometry such as:

```text
PointCloud.positions
Surface.vertices
VectorGlyphSet origins/vectors
```

Color-array changes do not use equivalent fast paths.

Decision:

- future visual attribute implementation must include value/color buffer updates in place;
- do not classify current geometry update performance as proof of animated continuous-colormap performance.

## 13. Scene schema changes are explicit gates

Current persistent Scene format is:

```text
spectra.scene v4
```

Decision:

- Phase 1 presentation should use existing ordinary primitives/resources and avoid schema churn;
- generic visual attributes/environment/background become explicit schema-evolution checkpoints if persisted in Scene;
- old readers/fixtures/migration behavior must be considered before v5.

## 14. Presentation resource identities are deterministic

Decision:

- scientific IDs remain untouched;
- presentation-owned IDs use reserved semantic namespaces such as `presentation.camera.*`, `presentation.light.*`, `presentation.legend.*`;
- no UUID/process-hash/native-name identity;
- repeated composition must be idempotent and avoid accumulating duplicate resources.

## 15. Premium showcase approval is layered

Decision:

Every showcase should report separately:

```text
scientific invariant PASS/FAIL
generic Scene PASS/FAIL
presentation PASS/FAIL
native backend PASS/FAIL
visual review
```

A beautiful screenshot alone is not a scientific/premium acceptance result.

## 16. Root package stays small; curated SDK is separate

Current root `spectra` intentionally exports very little.

Decision:

- do not turn `spectra/__init__.py` into a giant re-export surface;
- future third-party API lives under a curated `spectra.sdk` facade;
- add exports incrementally after the corresponding contracts are validated.

## 17. Runtime freeze before next validation remains intact

The executable numerical/experiments development batch ended at the recorded runtime checkpoint:

```text
00b5403a9ffb005b7eb011833174e013158ee1f4
```

Later work is intentionally architecture/docs/source audit only.

The next local validation therefore qualifies the executable delta from the last verified baseline through that runtime checkpoint rather than treating documentation work as new runtime behavior.

## Implementation implication after green validation

Recommended order remains:

```text
1 presentation immutable value contracts
2 preset resolution
3 deterministic resource IDs
4 Scene-local camera composition
5 title/time/basic light composition
6 timeline conflict handling
7 generic Scene tests
8 premium Maxwell/electrostatic showcase
9 visual-attribute runtime checkpoint
10 Blender premium attribute/native update path
```

Project/plugin/metadata/native CPU work should remain separate work packages unless a concrete dependency requires otherwise.

## Success criterion

The next runtime phase should begin with fewer architectural unknowns than the current phase ended with. Every new abstraction should reuse current authoritative registries/lifecycles where they already solve the problem, and new Core schema concepts should be introduced only where source audit has shown a real renderer-independent gap.
