# Spectra Science — Post-Green Implementation Task Board

Status: **execution plan after the pending `acb9e056... -> 00b5403...` runtime batch validates green**.

This board prevents another very large unchecked runtime batch. Each work package should land with its own narrow validation gate before moving to the next materially different foundation.

## Gate G0 — Pending numerical/experiments validation

Before any new executable feature work:

```text
pull latest main
compileall
full pytest
catalog/auto-discovery probe
solver role/policy/RK45 targeted tests
experiments/provenance/artifact targeted tests
```

If failures exist, fix root causes first.

Do not mix Premium Presentation implementation into G0 fixes.

Expected report includes actual test count and final green SHA.

## Track P — Premium Presentation

### W1 — Presentation value contracts and preset resolver

Scope:

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

Likely files:

```text
spectra/presentation_models.py
spectra/presentation_presets.py
spectra/presentation.py exports/integration
```

Do not change Scene schema.

Tests:

- deterministic preset resolution;
- explicit override wins;
- invalid numeric/range values rejected;
- preset defaults match `PRESENTATION_PRESET_DEFAULTS.md`.

Exit gate:

```text
compileall
presentation resolver tests
full pytest
```

### W2 — Camera fit and deterministic presentation IDs

Scope:

- Scene-local bounds only;
- `Transform3D.look_at()`;
- `presentation.camera.primary`;
- empty bounds handling;
- preserve/replace existing camera policy.

No Blender code.

Tests:

- one point;
- asymmetric bounds;
- non-default CoordinateFrame3D;
- existing camera preserve/force modes;
- idempotence.

Exit gate: full plain-Python green.

### W3 — Presentation composer skeleton

Scope:

```text
compose_presentation(scene, intent, context=None)
```

Passes:

- resolve;
- strip previous presentation-owned resources;
- capture scientific IDs;
- camera;
- final Scene validation.

Do not add lighting/legend/visual attributes yet if they enlarge patch materially.

Tests use `PRESENTATION_TEST_FIXTURES.md` F1-F5/F10.

### W4 — Basic labels/lights/axes

Scope current Scene v4 only:

- title/subtitle;
- simple time annotation contract;
- key/fill/rim generic Light resources;
- simple axes from Polyline/TextLabel/Group where appropriate.

No world/background schema.

Tests:

- deterministic resource IDs;
- no scientific bound contamination;
- recomposition resource count stable.

### W5 — Animation composition integration

Scope:

- reveal policy;
- `staggered_reveal` reuse/refactor;
- conflict detection before merge;
- scientific `(target_id, property_path)` ownership wins.

Do not implement generic track blending.

Tests:

- scientific geometry track + presentation opacity track;
- direct trim_end conflict;
- opacity conflict;
- duration merge;
- repeated composition.

### W6 — Generic Phase 1 presentation full gate

Run all `PRESENTATION_TEST_FIXTURES.md` plain tests through MemoryBackend/BackendSession.

Exit:

- input Scene immutable;
- scientific IDs preserved;
- deterministic/idempotent output;
- no renderer imports;
- full suite green.

Only after W6 is green begin Blender premium work.

## Track B — Blender Premium

### B1 — Generic composed Scene native smoke

No new backend representation.

Feed W6 Scenes into current `IncrementalBlenderBackend`.

Validate:

- camera;
- lights;
- text;
- axes;
- scientific geometry;
- cleanup.

### B2 — Camera/light/text incremental fast paths

Add only native presentation-heavy update paths.

Exit:

- object identity stable;
- counts stable;
- no scientific geometry rebuild for camera/light-only changes.

### B3 — Material lifecycle

Avoid native material accumulation on repeated apply/preset changes.

Exit:

- stable owned material count;
- quantitative unlit colors preserved;
- cleanup safe.

### B4 — Ownership metadata/inspection

Add backend-private Spectra semantic/presentation ownership metadata where useful.

No project source-of-truth stored in Blender pointers.

## Track A — Generic Visual Attributes / Scene v5

This track is deliberately after basic Premium Presentation so W1-W6 do not depend on schema migration.

### A1 — VisualAttribute value model

Implement:

```text
association: vertex/instance/primitive
kind: scalar/vec2/vec3/color
name
values
quantity metadata
```

No Scene integration yet if separate value-level tests are cleaner.

### A2 — Primitive attachment and validation

Attach generic attributes to supported primitives according to final API design.

Validate counts/association.

### A3 — Scene v5 serialization

- bump schema only here;
- preserve v1-v4 reads;
- encode/decode visual attributes;
- malformed attributes rejected;
- historical fixtures remain readable.

Full serialization suite required.

### A4 — BackendCapabilities additive extension

Add conservative defaults.

Current backends remain source-compatible.

Do not mark Blender feature true until implementation passes.

### A5 — Blender static attribute mapping

Start with one strongest proof:

```text
Surface vertex scalar/color
```

One mesh, one scalable attribute-driven material path.

### A6 — Blender incremental attribute updates

Animate attribute values with same topology.

Exit:

- object + mesh identity stable;
- material count stable;
- no per-value material explosion;
- timeline playback count/leak stable.

### A7 — PointCloud / VectorGlyphSet attribute migration

Replace/fallback beyond current high-cardinality material-slot approach.

Preserve existing categorical path where useful.

## Track S — Public SDK and Plugins

Begin only after presentation/public boundaries settle enough to expose.

### S1 — `spectra.sdk.scene`

Curate Scene/primitives/types/units/transforms/materials only.

No root `spectra` namespace explosion.

### S2 — `spectra.sdk.domain`

Curate DomainModule/Dependency/Registry/Catalog/Descriptor.

### S3 — `spectra.sdk.numerics`

Curate numerical descriptors/requirements/policy/provenance.

### S4 — `spectra.sdk.experiments`

Curate public experiment value contracts/artifacts.

### S5 — SDK import smoke

Fresh interpreter imports for every facade.

### S6 — In-process PluginDescriptor/PluginRegistry

No environment entry-point scanning yet.

- descriptor add/remove;
- enable/disable;
- dependency/version diagnostics;
- candidate catalog built from built-ins + enabled plugin factories;
- candidate discarded on conflict.

### S7 — Sample optics plugin fixture

Use `PLUGIN_SDK_QUICKSTART.md`.

Prove capability-driven load and generic Scene visualization.

### S8 — Python entry-point discovery adapter

Only after in-process plugin lifecycle is green.

Discovery returns descriptors; normal PluginRegistry handles activation.

## Track J — Project Runtime

### J1 — Project immutable record types

Metadata, model, solver selection intent, result references, views, presentations, requirements.

### J2 — deterministic JSON round-trip

Schema `spectra.project v1` only after migration/fixture policy is ready.

### J3 — reference validation

Duplicate/broken IDs rejected.

### J4 — invalidation graph

Model -> result -> view -> presentation.

Presentation-only edits do not stale result.

### J5 — environment/plugin requirement diagnostics

No auto-install/auto-enable.

### J6 — canonical project fixtures

Implement examples from `PROJECT_V1_CANONICAL_EXAMPLES.md`.

### J7 — ProjectRuntime compile_view/present

Reuse DomainRegistry, VisualizationRegistry, presentation composer.

No Blender dependency.

## Track N — Native CPU Numerical Provider

Begin after G0 green. It can run in parallel with later presentation work only if changes do not collide; otherwise keep serial.

### N1 — provider package skeleton

Separate optional package/provider.

### N2 — native fixed-step RK4 contract proof

Register:

```text
ode.first_order / rk4.native_cpu
```

Do not make default.

### N3 — analytical parity/order

Exponential, oscillator, multi-state, observed order ~4.

### N4 — policy/explicit dispatch and provenance

`cpu`, float64, non-reference selection.

### N5 — one high-level vertical slice

Mechanics or small method-of-lines PDE changes implementation without source edits.

### N6 — benchmark/report

Separate callback/packing/native/materialization time.

No speed claim if Python RHS dominates.

### N7 — batched/native RHS follow-up

Only based on measured bottlenecks.

## Track G — GPU

Do not begin merely because hardware is available.

Prerequisites:

- native CPU provider contract green;
- numerical buffer/ownership proven;
- batch use case defined;
- parity/convergence harness reusable.

Then:

```text
G1 batched GPU ODE proof
G2 GPU grid operators
G3 device-resident PDE pipeline
G4 persistent device buffers
G5 optional renderer interop
```

Each is separate.

## Cross-track rule — no 100-commit unchecked batch

A foundation-changing package should generally end with:

```text
compileall
focused tests
full pytest
```

Native Blender changes also get targeted Blender validation.

Schema changes get historical-fixture migration tests.

Native numerical changes get parity/convergence.

Do not wait across multiple independent foundation changes before testing again.

## Commit discipline

Prefer one conceptual work package per small series of commits.

Do not mix:

```text
presentation + Scene schema + Blender Geometry Nodes + native solver
```

in one validation checkpoint.

This makes regression diagnosis tractable.

## Promotion/status language

For every package distinguish:

```text
design
implemented/unverified
plain-Python verified
native-target verified
stress/performance verified
```

A doc/API draft is never reported as runtime capability until implemented.

## Recommended immediate sequence after G0

If G0 is fully green:

```text
W1 preset/value contracts
W2 camera fit
W3 composer skeleton
W4 labels/lights/axes
W5 timeline ownership/reveal
W6 full generic presentation gate
B1 Blender composed-scene smoke
B2 presentation incremental updates
```

Then choose between:

```text
A-track visual attributes
or
N-track native CPU
```

based on product priority.

For visible product progress, A-track + Blender quantitative coloring is likely more immediately impressive.

For execution-platform proof, N-track demonstrates solver interchangeability.

They should remain independent.

## Success criterion

After G0, every major architectural promise is converted through small, independently validated work packages instead of another monolithic development wave. The project should always have a recent trustworthy green checkpoint.