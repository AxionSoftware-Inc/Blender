# Spectra Science — Implementation Work Packages

Status: **planning document; no runtime implementation implied**.

This document breaks the post-validation roadmap into bounded work packages so cross-cutting changes are not stacked into another very large unchecked runtime batch.

Each package should ideally end with its own green checkpoint.

## Gate W0 — qualify current numerical runtime

Executable delta:

```text
acb9e056326177fac49cc57b202ca80cca5090a7
    ->
00b5403a9ffb005b7eb011833174e013158ee1f4
```

Required:

```text
compileall
full pytest
DomainCatalog probe
solver role/policy/RK45/provenance targeted tests
experiments/artifact/tracing targeted tests
```

Output:

```text
new verified SHA
new test count
new domain/provider count
root fixes
```

No later runtime package starts before W0 is green.

---

# Product presentation track

## W1 — presentation value types

Scope:

- `PresentationIntent`;
- preset/policy enums/dataclasses;
- deterministic preset resolution;
- validation only.

No Scene mutation/composition yet if keeping the patch smaller is useful.

Tests:

- default presets;
- override resolution;
- invalid values;
- immutability.

Exit:

```text
full pytest green
```

## W2 — generic presentation composer

Scope:

- `compose_presentation()`;
- deterministic presentation IDs;
- title/subtitle/time labels;
- basic camera fit if existing Camera contract permits;
- current `staggered_reveal` integration;
- timeline merge.

Do not add quantitative colors yet.

Tests:

- Scene input not mutated;
- scientific IDs/geometry preserved;
- timeline composition;
- MemoryBackend inspection.

Exit:

```text
full pytest green
```

Optional targeted Blender smoke only if generic Scene/camera/light behavior changed materially.

## W3 — quantitative color semantics

Scope:

- `ColorScaleKind`;
- `RangeMode`;
- range resolution;
- quantity metadata;
- legend metadata;
- sequential/diverging proof.

Proofs:

```text
probability density -> sequential
potential -> diverging around explicit zero/reference
```

No Blender shader implementation yet if generic value transport is unresolved.

Exit:

```text
full pytest green
```

## W4 — cyclic phase + coordinated views

Scope:

- cyclic scale;
- quantum phase semantics;
- synchronized probability/phase view metadata;
- deterministic multi-view composition if supported.

Exit:

```text
quantum blueprint generic Scene green
full pytest green
```

## W5 — Blender premium basic adapter

Scope:

- world/theme;
- camera;
- basic scientific-studio light rig;
- title/labels;
- quantitative material mapping only for capabilities proven in generic layer;
- ownership/cleanup.

Do not add Geometry Nodes yet.

Native tests:

- Maxwell cinematic;
- electrostatic dark_lab;
- preset switch;
- identity/cleanup/no object leak.

Exit:

```text
plain suite green
Blender targeted premium native smoke green
```

## W6 — Blender dense premium representation

Scope:

- Geometry Nodes or attribute-based PointCloud/VectorGlyphSet representation where beneficial;
- per-instance color/scale;
- display LOD;
- incremental attribute updates.

Performance gate:

- compare with current batched curve/mesh reference;
- object count independent of glyph count;
- no regression in cleanup/identity.

---

# Introspection / SDK / plugin track

## W7 — minimal semantic metadata registry

Scope:

- metadata records;
- transaction-aware registration;
- derive domain/capability info from actual runtime;
- `EngineInspector`.

Proof domains:

```text
mathematics
mechanics
electromagnetism
experiments
```

Exit:

```text
full pytest green
```

## W8 — curated `spectra.sdk`

Scope:

Expose only stable infrastructure proven by prior packages.

Do not export every domain internal.

Tests:

- plain Python import without Blender/GPU;
- explicit export list;
- sample extension imports only supported surfaces.

## W9 — explicit in-process plugin descriptors

Scope:

- `PluginDescriptor`;
- `PluginRegistry`;
- enable/disable;
- compatibility/dependency plan;
- catalog composition.

No Python entry-point scanning yet.

Proof:

```text
sample optics plugin descriptor
```

Exit:

- plugin off: built-in environment unchanged;
- plugin on: optics capability loads transactionally.

## W10 — Python package entry-point adapter

Only after W9 proves the runtime model.

Scope:

- discover descriptors from installed packages;
- no auto-enable;
- deterministic diagnostics.

---

# Project/product track

## W11 — project document core

Scope:

- immutable `ProjectDocument` records;
- metadata/models/views/presentation references;
- deterministic JSON round-trip;
- environment requirements.

No large numerical arrays in JSON.

Exit:

```text
schema fixtures + full pytest green
```

## W12 — project runtime invalidation

Scope:

- model/result/view/presentation state;
- dirty/stale transitions;
- attach/detach results;
- renderer-independent project runtime.

Proof:

```text
presentation edit does not invalidate solve
model edit does invalidate solve
backend switch does not invalidate science
```

## W13 — command/undo layer

Scope:

- semantic commands;
- transaction/revision records;
- undo/redo;
- preview vs commit.

Do not implement collaboration yet.

## W14 — headless CLI minimum

Scope:

```text
inspect
validate
solve
view
present
export
```

Use runtime APIs; no duplicate scientific logic.

---

# Performance execution track

This track can proceed independently after W0 if it does not collide with another foundational registry refactor.

## P1 — native CPU RK4 provider

Role:

```text
ode.first_order / rk4.native_cpu
```

Requirements:

- reference parity;
- order ~4;
- provenance;
- explicit selection/fallback;
- high-level mechanics/PDE proof without domain code changes.

Do not introduce a general GPU buffer framework first.

## P2 — native adaptive provider or batched fixed-step

Choose based on P1 measurements.

Candidate A:

```text
rk45.native_cpu
```

Candidate B:

```text
batched rk4.native_cpu
```

Do not implement both simultaneously unless the ABI clearly supports both without churn.

## P3 — runtime numerical buffer contract

Promote only abstractions proven necessary by P1/P2.

Initial forms:

```text
contiguous scalar/vector state
uniform-grid scalar arrays
explicit dtype/shape/ownership
```

## P4 — GPU batched ODE

Scope:

- large independent case batches;
- transfer cost reporting;
- persistent buffers if beneficial;
- CPU fallback policy.

## P5 — GPU grid operators

Scope:

```text
laplacian
gradient
divergence
simple diffusion/transport
```

Only after parity infrastructure is mature.

## P6 — device-resident PDE pipeline

Goal:

Avoid round-tripping every stencil/intermediate array through Python/host memory.

This is a later optimization, not a prerequisite for first GPU proof.

---

# Remote/distributed track

## R1 — execution request/result records

Scope:

- serializable semantic execution request;
- environment requirements;
- job ID/revision;
- artifact return contract.

Local mock worker first.

## R2 — remote worker transport adapter

Only after local request/result semantics are proven.

No new science runs inside transport code.

## R3 — distributed experiments

Parameter cases can fan out to workers while preserving deterministic case IDs and environment/provenance metadata.

---

# Checkpoint naming

After each green work package, record a concise checkpoint in `CURRENT_STATUS.md`:

```text
W2 verified
commit: ...
pytest: ... passed
native Blender: targeted PASS / not required
notes: ...
```

Do not retain only a vague statement that “presentation works”.

# Merge/conflict guidance

Avoid parallel runtime edits to the same foundational areas:

```text
DomainRegistry
NumericalSolverRegistry
Scene schema
presentation core value types
ProjectDocument schema
```

Safe parallel work is more likely in:

```text
native provider implementation
showcase data/examples
documentation
visual reference design
headless tooling after APIs stabilize
```

# Package-size rule

A work package should prove one abstraction.

If a patch simultaneously adds:

```text
new Scene schema
new plugin system
new project format
new renderer adapter
new native solver
```

it is too broad.

# Priority recommendation

Product-facing priority after W0:

```text
W1 -> W2 -> W3 -> W5
```

This gets Spectra to the first visibly premium Blender result quickly while preserving renderer independence.

Then:

```text
W7 -> W8 -> W9 -> W11
```

for ecosystem/product structure.

Performance can proceed in parallel:

```text
P1 -> P2/P3 -> P4/P5
```

# Success criterion

Each completed package should leave Spectra with a new capability that is independently understandable, testable, revertible, and documented without forcing unrelated subsystems to change at the same time.