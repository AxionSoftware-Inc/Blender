# Spectra Science — System Architecture Map

This document is a compact map of the whole intended Spectra platform. It does not replace subsystem documents; it shows how they fit together.

## One-line architecture

```text
Authoring
  -> Project/semantic model
  -> capability graph
  -> numerical execution
  -> semantic result
  -> explicit scientific view
  -> base Scene/Timeline
  -> presentation policy
  -> renderer backend
  -> export/product surface
```

The central rule is that scientific meaning remains stable while execution, presentation, renderer, UI, and deployment can change independently.

## Layer map

```text
┌─────────────────────────────────────────────────────────────┐
│                     AUTHORING SURFACES                      │
│ Python │ Blender panel │ Standalone UI │ CLI │ AI │ import │
└──────────────────────────────┬──────────────────────────────┘
                               │ commands / project edits
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROJECT / STUDY MODEL                     │
│ models │ parameters │ resources │ experiments │ view refs  │
│ solver policies │ presentation variants │ revisions        │
└──────────────────────────────┬──────────────────────────────┘
                               │ semantic objects
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOMAIN SYSTEM                         │
│ DomainCatalog │ DomainRegistry │ capabilities │ semantics  │
│ math │ PDE │ physics │ chemistry │ relativity │ plugins    │
└──────────────────────────────┬──────────────────────────────┘
                               │ numerical roles / composition
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    NUMERICAL EXECUTION                      │
│ NumericalSolverRegistry │ policies │ provenance            │
│ Python reference │ native CPU │ GPU │ remote/HPC           │
└──────────────────────────────┬──────────────────────────────┘
                               │ solutions / fields / metrics
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    SCIENTIFIC RESULTS                       │
│ fields │ trajectories │ PDE histories │ diagnostics        │
│ experiment results │ uncertainty │ calibration             │
└──────────────────────────────┬──────────────────────────────┘
                               │ explicit view semantics
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 VISUALIZATION COMPILATION                   │
│ VisualizationRegistry │ explicit views                     │
│ PointCloud │ Polyline │ Surface │ VectorGlyphSet │ labels  │
│                 Scene + scientific Timeline                │
└──────────────────────────────┬──────────────────────────────┘
                               │ base Scene
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│ presets │ theme │ camera │ color scales │ legends │ axes   │
│ annotations │ lighting intent │ reveal/pacing │ quality    │
└──────────────────────────────┬──────────────────────────────┘
                               │ enriched Scene/presentation
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     RENDERER BACKENDS                       │
│ Memory │ Blender │ future WebGPU │ future other renderers  │
└──────────────────────────────┬──────────────────────────────┘
                               │ native representation/render
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCT / EXPORT                         │
│ interactive viewport │ image │ video │ report │ Scene JSON │
│ .blend cache/export │ project archive │ remote render      │
└─────────────────────────────────────────────────────────────┘
```

## Cross-cutting systems

Several systems span multiple layers without owning scientific meaning.

### Units and coordinates

Used by semantics, numerical adapters, imports, views, and project persistence.

Renderer coordinates must not replace scientific coordinates.

### Diagnostics

Structured diagnostics span:

```text
validation
capability loading
numerical execution
experiments
plugins
presentation
backend
serialization
```

See `DIAGNOSTICS_AND_ERRORS.md`.

### Reproducibility/provenance

Records:

- domain/capability versions;
- solver implementation/method/execution;
- policies;
- experiment traces;
- input resources where tracked.

Presentation reproducibility is related but separate from scientific reproducibility.

### Maturity/status

Every subsystem may be design/reference/experimental/etc. independently.

See `CAPABILITY_MATURITY_MODEL.md`.

### Security/trust

Project/data files are data; plugins/native providers are executable components requiring approval/trust policy.

See `TRUST_AND_SECURITY_MODEL.md`.

## Core vs non-Core

### Core should own

Only universal abstractions:

```text
basic value types
units/dimensions
coordinates/transforms
Scene primitives
Timeline
serialization infrastructure
safe expression infrastructure
generic composition/contracts
```

### Domain layer owns

Scientific meaning:

```text
calculus
PDE
mechanics
Maxwell
quantum
chemistry
relativity
future biology/optics/etc.
```

### Numerical execution layer owns

How a stable numerical role is executed.

It must not redefine physics.

### Presentation owns

How a correct Scene is communicated visually.

It must not modify solver data.

### Backend owns

Native renderer realization.

It must not calculate missing science.

### Product/UI owns

Workflow, jobs, user interaction, saving, remote execution orchestration.

It must not become the authoritative scientific model.

## Main dependency direction

Preferred direction:

```text
product -> project/domain APIs
scientific high-level domain -> lower capability contracts
visualization -> generic Scene
presentation -> Scene/policy
backend -> Scene/presentation
```

Forbidden inverse dependencies:

```text
Core -> Blender
physics -> Blender
physics -> CUDA
project semantics -> UI widgets
solver semantics -> presentation style
renderer -> hidden scientific formulas
```

## Domain extension path

A new scientific subject normally enters here:

```text
new domain semantics
    ↓
reuse existing capabilities
    ↓
add subject-specific laws/diagnostics
    ↓
explicit/default view
    ↓
generic Scene
```

It should not require changes to:

- Blender backend;
- Timeline;
- solver registry unless genuinely new numerical role needed;
- project UI;
- every other domain.

## Numerical provider extension path

A faster implementation enters here:

```text
stable solver role
    ↓
provider domain/plugin
    ↓
register implementation + method/execution metadata
    ↓
solver policy selects it
```

High-level scientific code remains unchanged.

## Renderer extension path

A renderer enters here:

```text
Scene + presentation intent
    ↓
backend capability profile
    ↓
native resources
```

No scientific domain changes required.

## Product surface extension path

A new UI/client enters above the project/semantic APIs:

```text
new UI
  -> same project commands
  -> same engine
```

A standalone WebGPU app and Blender panel should not become two different scientific implementations.

## Persistent data boundaries

Durable source-of-truth:

```text
project semantic records
external resource identities
experiment/provenance artifacts
presentation policy records
```

Derived/rebuildable:

```text
numerical caches
base Scene caches
presentation caches
Blender objects
WebGPU buffers
render outputs
```

A renderer-native file may be useful but should not be the only durable scientific model.

## Remote execution boundary

Remote workers sit under numerical execution, not above domains.

```text
same semantic problem
  -> execution request
  -> worker/provider
  -> same semantic result contract
```

Presentation/rendering can happen on another machine later.

## Current verified vs designed map

### Verified milestone

At recorded `acb9e056...`:

- 224 tests passed;
- DomainCatalog passed;
- Blender 5.2 native smoke passed;
- incremental identity/batching/cleanup/leak behavior validated.

### Implemented after that milestone but awaiting next full validation

Large numerical/experiment/solver-policy/adaptive/provenance batch.

### Design/spec only today

Examples include:

- premium presentation runtime phases;
- public `spectra.sdk` facade;
- external plugin entry-point discovery;
- project document runtime;
- native/GPU numerical providers;
- remote worker runtime.

Do not confuse these layers in status reporting.

## Key source-of-truth docs

```text
DOMAIN_SYSTEM.md
DOMAIN_CATALOG.md
SOLVERS_AND_EXPERIMENTS.md
PREMIUM_PRESENTATION_SYSTEM.md
PROJECT_STATE_MODEL.md
MODULE_SDK.md
NATIVE_NUMERICAL_BACKENDS.md
BLENDER_BACKEND.md
POST_VALIDATION_IMPLEMENTATION_PLAN.md
```

Use `docs/README.md` for the full index.

## Success criterion

Spectra is architecturally healthy when adding a new science module, numerical provider, renderer, UI surface, or remote worker changes only the layer that logically owns that extension and leaves the rest of the platform connected through stable contracts.
