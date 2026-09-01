# Spectra Science — Project and Study Document Model

This document defines the intended persistent project layer above individual scientific semantics, experiment artifacts, and renderer-neutral Scenes.

The project document runtime is not yet implemented. This contract exists so product/UI/backend work does not accidentally make Blender files or UI state the authoritative scientific project format.

## Goal

A user-facing Spectra project should be able to describe conceptually:

```text
scientific inputs / model
solver/execution policy
experiments/studies
presentation intent
compiled Scene caches
provenance
external data references
```

without depending on Blender as the storage format.

A `.blend` file may be an output/cache/work session, but it should not be the only source of scientific truth.

## Layering

Spectra should distinguish at least four persistence layers.

### 1. Scientific model document

Describes what the user wants to study:

- domain/model type;
- parameters;
- units;
- boundary/initial conditions;
- source definitions;
- requested outputs/views;
- solver-role requirements/policies when specified.

### 2. Study/experiment records

Describe executed parameter sweeps/calibration/convergence and their metrics/provenance.

Existing schema-versioned experiment artifacts are the foundation for this layer.

### 3. Presentation document

Describes how the result should be communicated:

- preset;
- theme;
- camera policy;
- color scales;
- legends;
- axes;
- annotations;
- animation/pacing;
- explicit presentation overrides.

### 4. Scene/render cache

A versioned `spectra.scene` document may cache compiled renderer-neutral geometry/timeline for fast reopen/render.

It is derived data and should be invalidatable when scientific/presentation inputs change.

## Proposed project envelope

Conceptually:

```text
SpectraProject
    schema/version
    project metadata
    environment requirements
    models/studies
    presentation configurations
    artifact references
    scene-cache references
    external data references
```

Possible JSON-like structure:

```json
{
  "schema": "spectra.project",
  "version": 1,
  "metadata": {...},
  "environment": {...},
  "models": [...],
  "studies": [...],
  "presentations": [...],
  "artifacts": [...],
  "scene_caches": [...],
  "data": [...]
}
```

The exact runtime schema should be introduced only with migration/validation tests.

## Project metadata

Reasonable generic metadata includes:

- project ID;
- title;
- description;
- created/modified timestamps where product layer needs them;
- optional author/application metadata;
- tags.

Scientific meaning must not depend on human-readable title strings.

## Scientific model instances

A project may contain multiple scientific model instances.

Examples:

```text
electrostatic_problem
maxwell_problem
heat_problem
elastic_problem
reaction_network
experiment_definition
```

Each model record should identify:

- semantic model type/version;
- stable model ID;
- serialized parameters;
- units;
- links/references to other model records when composing multiphysics;
- external data references where required.

Do not serialize Python class import paths as the only semantic identifier if a stable schema/type identifier can be provided.

## Composition references

Multiphysics projects require explicit relationships.

Examples:

```text
reaction_diffusion.output.temperature_source
    -> heat_problem.source

heat_solution.temperature
    -> thermoelastic_problem.temperature

maxwell.E/J
    -> electrothermal heat source
```

The project layer should record semantic connection intent rather than copying generated arrays between every node unless cached artifacts are intentionally stored.

A future visual/node editor can be a UI over this graph; the graph should not exist only as UI widget state.

## Solver policy storage

Projects may optionally request numerical execution requirements/policies.

Examples:

```text
prefer GPU float32, fallback CPU
require adaptive order >= 4
force rk4.reference for reproducibility study
```

Rules:

- stable solver role remains semantic numerical contract;
- project may store selection policy/requirements;
- project should not require a specific device ID unless the user explicitly pins one;
- unavailable implementation should produce a clear compatibility decision, not silent semantic downgrade.

## Environment requirements vs environment snapshot

Distinguish:

### Requirements

What must be available to run/reopen the project:

- required capabilities/versions;
- optional plugin IDs/API compatibility;
- required semantic schemas.

### Snapshot

What was actually loaded/used for a particular run:

- domains;
- capabilities/providers;
- solver implementations;
- policies;
- execution metadata;
- plugin/package provenance later.

A project may be runnable in a newer compatible environment while old study artifacts retain their original fingerprints.

## Experiments and study artifacts

Do not embed huge arbitrary runtime solution objects into the main project JSON by default.

Prefer references to durable study artifacts:

```text
project
    -> study definition
    -> experiment artifact summary
    -> optional large result data file/cache
```

This keeps project metadata inspectable and allows large numerical results to use appropriate storage formats.

## External numerical data

Large arrays/meshes/volumes should eventually use dedicated data resources rather than JSON lists when scale demands it.

The project document should reference them with metadata such as:

- resource ID;
- relative/managed URI;
- content hash;
- format/schema;
- shape/dtype/unit metadata;
- optional compression/chunking.

Do not silently depend on an absolute local filesystem path with no integrity metadata for a portable project.

## Scene caches

`Spectra Scene` is a useful renderer-neutral cache/output.

A scene-cache record should identify which inputs produced it, potentially through fingerprints of:

```text
scientific model state
study/result artifact
presentation intent
scene schema/compiler version
```

If any authoritative input changes, stale Scene caches should be invalidated/recompiled.

The cache should not override newer scientific state merely because it exists.

## Blender project relationship

Blender may save a `.blend` file containing Spectra-generated native objects.

Recommended model:

```text
Spectra project = authoritative scientific/presentation project
.blend = renderer-specific work/render cache/output
```

When useful, the Blender file may contain/link the Spectra project ID/fingerprint and presentation metadata for round-trip identification.

It should not force scientific domains to serialize Blender object names as model IDs.

## Editing in Blender

A future product must decide which Blender edits are:

### presentation edits

Potentially round-trippable:

- camera composition override;
- theme/material presentation override;
- label placement;
- render quality.

### scientific edits

Must update Spectra semantic/project state through an explicit interface:

- source position;
- boundary condition;
- physical parameter;
- solver setting.

### arbitrary renderer edits

May remain Blender-only and not round-trip into scientific semantics.

The system should never guess that moving a Blender mesh necessarily changes a scientific source unless ownership/mapping contract says so.

## Presentation variants

One scientific study may have multiple presentation configurations:

```text
analysis view
publication figure
cinematic demo
teaching sequence
```

These should reference the same scientific result/model rather than duplicate computation unnecessarily.

Conceptually:

```text
study result
    -> presentation.analysis
    -> presentation.publication
    -> presentation.cinematic
```

## Project-level stable IDs

Use stable IDs for:

- models;
- study definitions;
- result artifacts;
- presentation variants;
- data resources;
- scene caches.

Do not rely on array order or human titles as persistent identity.

## Deterministic fingerprints

Useful project subgraphs may have fingerprints to support:

- cache invalidation;
- reproducibility;
- render farm deduplication;
- comparison;
- collaborative synchronization later.

Possible fingerprints:

```text
model_fingerprint
study_definition_fingerprint
presentation_fingerprint
scene_cache_fingerprint
```

These are separate from environment fingerprint.

## Collaboration future

A clean semantic project graph makes collaboration possible later without synchronizing raw Blender datablocks.

Potential collaboration operations:

- edit model parameter;
- add/remove source;
- change study definition;
- add presentation variant;
- attach result artifact;
- comment/annotate.

Conflict semantics should operate on project/model IDs rather than renderer object creation order.

No collaboration runtime is implied by this document yet.

## UI relationship

A standalone desktop/web/Blender UI should be a projection/editor of project state.

Bad architecture:

```text
UI controls = only copy of scientific parameters
```

Desired:

```text
project semantic state
    -> UI representation
    -> edits produce validated project/model changes
```

This lets multiple UI surfaces exist:

- Blender panel;
- standalone desktop app;
- WebGPU browser client;
- CLI;
- AI authoring surface.

## AI authoring relationship

AI may generate/edit project/model intents, but the project must validate through deterministic domain/unit/capability contracts.

AI should not write arbitrary Blender Python as the authoritative scientific project format.

## Security and portability

Project documents should not execute arbitrary code merely by being opened.

Semantic model identifiers should resolve through installed/trusted domain/plugin contracts.

External plugins themselves are executable trusted code, but the data document should remain declarative where practical.

## Schema migration

A `spectra.project` schema must be versioned from the start.

Rules:

- readers validate schema/version;
- migrations are explicit;
- old project compatibility is tested;
- scientific meaning must not silently change during migration;
- large external result resources may have independent format versions.

## Suggested implementation phases

### Phase 1

Define small project envelope for:

- project metadata;
- one/many model records;
- presentation references;
- experiment artifact references.

### Phase 2

Add schema-versioned JSON serialization and validation.

### Phase 3

Add cache fingerprints and Scene cache references.

### Phase 4

Add large numerical resource abstraction.

### Phase 5

Integrate Blender project linking/import/export.

### Phase 6

Use the same project model from standalone/WebGPU UI.

### Phase 7

Collaboration/synchronization only after stable semantic editing contracts exist.

## What the project format must not become

Do not:

- use `.blend` as the only scientific source of truth;
- serialize native renderer objects into scientific model records;
- store UI widget state as the sole parameter model;
- hide units in display strings;
- embed arbitrary executable Python in ordinary project data by default;
- conflate presentation preset with solver accuracy;
- silently reuse stale Scene/result caches after scientific inputs change;
- require one backend to open the scientific project.

## Success criterion

A Spectra project should be able to move between Blender, a future WebGPU/desktop client, a headless compute worker, and a saved study archive while preserving the same scientific model, execution provenance, and presentation intent.
