# Spectra Science — Cache and Artifact Storage Architecture

This document defines how Spectra should cache expensive intermediate/results and store durable artifacts without confusing derived data with scientific source of truth.

## Goal

Separate durable semantic state from rebuildable caches:

```text
project/model source
    ↓
solver/result artifacts
    ↓
derived fields/views
    ↓
Scene/presentation caches
    ↓
renderer-native caches
```

Each layer has different invalidation, portability, and storage requirements.

## Storage classes

Useful classes:

```text
durable project source
immutable scientific result artifact
experiment artifact
derived scientific cache
Scene cache
presentation cache
renderer-native cache
external resource cache
temporary execution scratch
```

## Durable project source

Contains user-authored scientific intent and configuration.

Examples:

- model parameters;
- resource references;
- solver policies;
- experiment definitions;
- view definitions;
- presentation variants.

This should be portable and versioned.

It should not depend on local Blender object IDs or GPU pointers.

## Scientific result artifact

A solved result is logically immutable and tied to:

```text
model revision/fingerprint
input resource identities/hashes
solver role/implementation
numerical settings
execution provenance
```

Changing presentation does not invalidate it.

A future project may retain several result artifacts for history/comparison.

## Experiment artifact

Current experiment artifact architecture already stores durable metric/parameter/environment summaries.

Future storage may optionally reference raw per-case result artifacts rather than embed them all.

This enables large sweeps to keep compact summaries while retaining selected raw cases.

## Derived scientific caches

Examples:

```text
vorticity derived from velocity history
field interpolation structure
spatial index
mesh adjacency
principal stress history
probability current
```

A derived cache key should include only upstream result/config that affects it.

Do not recompute a three-hour base simulation merely because a derived field cache is missing.

## Scene cache

A base Scene cache is tied to:

```text
result/view definition
display sampling
view compiler version
```

It should not depend on Blender.

Presentation changes may reuse it.

## Presentation cache

Presentation-enriched Scene/resources are tied to:

```text
base Scene identity
presentation intent
backend capability-independent presentation compiler version
```

Backend-native interpretations are a separate cache class.

## Renderer-native cache

Examples:

- Blender mesh/curve/material datablocks;
- Geometry Nodes groups;
- WebGPU buffers;
- renderer shader pipelines.

These are ephemeral/rebuildable from semantic Scene/presentation inputs.

A renderer-native cache may be invalid after:

- renderer version change;
- backend implementation change;
- device/driver change;
- Scene/presentation change.

Do not treat it as durable scientific data.

## External resource cache

Large remote/imported resources may be cached locally by content hash/logical resource identity.

Useful metadata:

```text
resource id
content hash
source URI
size
last verified
local cache path
```

Cache policy should avoid duplicating huge files unnecessarily.

## Execution scratch

Temporary files/buffers used during solve/render should have explicit lifecycle and may be deleted after completion/failure.

Examples:

- native temporary arrays;
- GPU staging data;
- remote worker scratch;
- render intermediates.

They should not become project dependencies accidentally.

## Cache keys

Cache identity should be semantic, not timestamp-only.

Conceptually:

```text
hash(
  upstream fingerprints,
  operation/view id,
  operation parameters,
  relevant implementation/schema version
)
```

Examples:

```text
result cache key = model fingerprint + execution plan fingerprint
view cache key = result id + view config fingerprint
presentation cache key = view Scene fingerprint + presentation intent fingerprint
```

## Fingerprints

A fingerprint should be deterministic for the content/contract it represents.

Do not include irrelevant volatile metadata such as wall-clock time in a content hash.

When a provider is non-deterministic, the result artifact still gets its own identity; cache reuse policy may be more conservative.

## Model fingerprint

A future model fingerprint may include:

- semantic model type/version;
- parameter values/units;
- boundaries/initial conditions;
- referenced resource hashes;
- plugin semantic versions.

It should not include presentation settings.

## Execution plan fingerprint

May include:

- solver role/selected provider;
- method;
- precision;
- timestep/tolerance;
- solver-specific numerical options;
- relevant provider version/build.

Policy fingerprint alone may be insufficient if it resolves differently on another machine; the actual selected implementation should be recorded in result provenance.

## Cache reuse across providers

Normally a numerical result from one provider should not be treated as identical to another provider's result merely because the semantic model is the same.

Both may be scientifically equivalent within tolerance but have different provenance.

For reproducibility, keep distinct result artifacts.

Derived views may reuse either result explicitly selected by the user/project.

## Cross-machine cache reuse

Portable caches:

- validated semantic result artifacts;
- experiment artifacts;
- renderer-neutral Scene caches if schema/version compatible.

Non-portable caches:

- raw GPU buffers;
- Blender runtime object handles;
- device-specific compiled kernels.

Storage metadata should state portability class.

## Cache invalidation

Use the project invalidation model.

### Physical parameter change

Invalidates:

```text
result
derived scientific cache
view Scene
presentation
renderer
```

### Solver provider/settings change

Invalidates result downstream, not semantic model.

### View change

Invalidates view/presentation/renderer only.

### Presentation change

Invalidates presentation/renderer only.

### Renderer update

May invalidate renderer-native cache only.

## Stale cache detection

Never trust cache presence alone.

Validate:

```text
schema/version
fingerprint
resource availability
provider/build compatibility where relevant
```

If uncertain, discard/rebuild cache rather than silently use stale scientific data.

## Storage layout

A future local workspace might conceptually use:

```text
project/
  project.json
  resources/
  artifacts/
    results/
    experiments/
  caches/
    derived/
    scenes/
    presentation/
    renderer/
```

Exact filesystem layout is product implementation detail.

The durable/cache distinction is the important contract.

## Large numerical arrays

Large result fields/histories should not be forced into giant JSON payloads.

Use a semantic metadata envelope referencing chunked/binary array storage.

Potential future storage technologies may include:

- HDF5;
- Zarr;
- custom typed chunk format;
- memory-mapped files;
- object storage chunks.

The semantic schema should remain independent from the storage engine.

## Chunking

Time-dependent/grid results may benefit from chunking by:

```text
time
spatial blocks
components
cases
```

Chunking should support partial view/analysis access without materializing the full result.

Example:

```text
load temperature z-slice at t=2s
```

should not necessarily read an entire 256^3 x 1000-step history.

## Compression

Compression is storage policy.

Do not use lossy compression for scientific arrays unless the project/result explicitly declares acceptable error/quantization semantics.

Presentation/video compression is separate.

## Cache quotas

Product layer may enforce:

- maximum cache size;
- LRU cleanup;
- per-project quotas;
- renderer cache cleanup;
- remote resource cache policy.

Evicting a rebuildable cache must not delete durable project/result artifacts unless explicitly configured.

## Result retention policy

Users/projects may choose:

```text
keep latest only
keep all successful results
keep selected/approved results
keep metrics only for sweep cases
```

This is project/storage policy, not solver behavior.

## Remote artifacts

Remote workers may publish result artifacts to shared/object storage and return content IDs/URIs.

Client project records them by semantic artifact identity and provenance.

If downloaded later, content hash/integrity can be verified.

## Failure cleanup

A failed solve/render should clean incomplete temporary artifacts unless they are intentionally retained for debugging.

Do not mark a partially written result as current/complete.

Use atomic publish pattern where practical:

```text
write temporary
validate/finalize
publish/rename to complete artifact id
```

## Serialization compatibility

Artifact metadata uses versioned schemas from `SCHEMA_VERSIONING_POLICY.md`.

A new Spectra version may discard incompatible caches while still reading durable project/result metadata when supported.

## Security

Cache/resource filenames/paths come from trusted storage logic, not arbitrary unsanitized project IDs.

Remote artifact retrieval follows trust/resource policy.

Do not deserialize unsafe executable objects from caches.

## Observability

Cache hit/miss/size/materialization metrics should be available to performance diagnostics.

This helps distinguish slow solving from repeated unnecessary resource loading or renderer rebuilding.

## Success criterion

Spectra should be able to keep expensive scientific results reusable across view/presentation/renderer changes, discard stale renderer/performance caches safely, move durable artifacts between machines, and avoid recomputation caused by treating every layer as one monolithic cache.
