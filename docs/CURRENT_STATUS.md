# Spectra Science — Current Status

This document is a concise status checkpoint separating **verified runtime behavior**, **implemented-but-awaiting-validation runtime work**, and **design/documentation work**.

It exists to prevent later agents/developers from inheriting stale green claims or mistaking design documents for implemented runtime features.

## Last fully reported verified runtime milestone

Commit:

```text
acb9e056326177fac49cc57b202ca80cca5090a7
```

Reported validation:

```text
compileall spectra: PASS
pytest: 224 passed
initial failures: 0
DomainCatalog / auto-discovery: PASS
106 unique deterministic domains
403 providers
Blender 5.2 LTS targeted native smoke: PASS
repo clean / synced at that milestone
```

Native Blender validation at/through the recorded milestones included:

- static curve/surface/material/light/camera creation;
- animated wave geometry updates;
- E/B VectorGlyphSet animation;
- stable Blender object/datablock identity;
- topology fallback;
- cleanup/orphan behavior;
- 10k PointCloud batching;
- 10k VectorGlyphSet batching;
- repeated-frame leak checks.

This is the current **verified baseline**, not a claim about every later runtime commit.

## Implemented runtime batch after the verified baseline

After `acb9e056...`, a large numerical/experiment/runtime refactor was implemented.

Major implemented areas include:

- `NumericalSolverRegistry` interoperability;
- stable `ode.first_order` role;
- role-dispatched high-level ODE/PDE/physics consumers;
- RK4 reference provider;
- Heun/RK2 reference provider;
- adaptive Dormand-Prince/RK45 provider;
- solver execution metadata and policies;
- problem compatibility predicates;
- ordered policy fallback;
- fixed/adaptive numerical provenance;
- requested vs accepted steps;
- dynamic 3D method-of-lines provenance;
- deterministic parameter sweeps;
- batched experiments;
- solver comparisons;
- convergence studies;
- sensitivity;
- deterministic uncertainty propagation;
- calibration;
- ranking/Pareto analysis;
- reproducibility/environment fingerprints;
- experiment JSON artifacts;
- per-case numerical execution tracing.

The last runtime-code checkpoint before the documentation-only architecture block is:

```text
00b5403a9ffb005b7eb011833174e013158ee1f4
```

This runtime batch still requires the next full local validation before receiving a new green test-count/qualification claim.

## Runtime freeze after `00b5403...`

Repository comparison from:

```text
base: 00b5403a9ffb005b7eb011833174e013158ee1f4
head: current main at the time this status was written
```

showed only:

```text
README.md
docs/*
```

changes.

No `spectra/` runtime source file changed in that documentation block.

Therefore the next local runtime validation should primarily qualify the executable delta:

```text
acb9e056... -> 00b5403...
```

while the later documentation commits can be reviewed for correctness without adding runtime behavior.

## Documentation/design block after runtime freeze

The docs-only block specifies future architecture for:

### Premium presentation

- renderer-neutral presentation intents/presets;
- visual design system;
- color scales/legends/axes/camera/lighting;
- deterministic presentation IDs/ownership;
- Blender premium mapping/acceptance;
- showcase scenarios.

### Product/project platform

- project lifecycle/invalidation;
- project document model;
- commands/undo;
- collaboration/revisions;
- templates;
- caches/artifact storage;
- UI information architecture;
- headless/CLI;
- export/reporting;
- data ingestion/resources.

### SDK/plugin ecosystem

- Module SDK;
- sample third-party extension blueprint;
- public `spectra.sdk` facade design;
- plugin packaging/discovery;
- API stability/deprecation;
- schema versioning;
- naming conventions;
- semantic metadata/introspection.

### Performance/execution future

- native/GPU provider contract;
- numerical buffer/data-layout design;
- validation/reference cases;
- performance budgets;
- observability/profiling;
- remote/HPC worker contract;
- high-performance roadmap.

### Governance/quality

- maturity/verification model;
- diagnostics/errors;
- trust/security;
- test strategy/checkpoints;
- release qualification;
- product milestones;
- AI authoring contract.

These documents are **design contracts**, not claims that the described runtime layers are already implemented.

## Current status categories

### Verified

- semantic engine foundation through recorded `acb9e056...` milestone;
- 224-test reported baseline;
- DomainCatalog/provider graph at that milestone;
- Blender 5.2 native reference/incremental smoke behavior at that milestone.

### Implemented, awaiting next full local validation

- post-`acb9...` numerical solver-role/interchangeability/adaptive/provenance/experiment runtime batch through `00b5403...`.

### Designed/documented, not yet implemented runtime

Examples:

- full premium presentation semantics/composer;
- quantitative presentation color/legend runtime;
- Blender premium adapter;
- `spectra.sdk` public facade;
- external plugin entry-point runtime;
- Spectra project runtime/schema;
- semantic metadata/introspection runtime;
- command/collaboration runtime;
- native CPU/GPU solver providers;
- remote/HPC worker runtime;
- standalone/WebGPU product surface.

## Next validation gate

When local resources/agent are available, run against latest `main` but interpret failures in the executable runtime delta.

Minimum:

```text
python -m compileall spectra
pytest -q
DomainCatalog / auto-discovery probe
solver role/policy/adaptive/provenance targeted tests
experiments/reproducibility/artifact/tracing targeted tests
```

Blender full native benchmark is not required solely because docs changed. Backend runtime did not change in the docs-only block.

If the runtime batch is green, record:

```text
new final SHA
new pytest count
domain/provider count
root fixes if any
new verified baseline
```

Then begin runtime implementation from `POST_VALIDATION_IMPLEMENTATION_PLAN.md`.

## Recommended first runtime work after green validation

Highest-value product sequence:

```text
Presentation semantic types
    -> Presentation composer
    -> quantitative color scales + legends
    -> five canonical premium Scenes
    -> Blender premium presentation adapter
```

A parallel performance track may begin with:

```text
native CPU first-order solver provider
    -> prove provider/buffer boundary
    -> later GPU providers
```

Do not start both with incompatible foundational refactors before establishing clean checkpoints.

## Source-of-truth navigation

Start with:

```text
README.md
docs/README.md
docs/SYSTEM_ARCHITECTURE_MAP.md
docs/POST_VALIDATION_IMPLEMENTATION_PLAN.md
```

Use `CAPABILITY_MATURITY_MODEL.md` to distinguish verified/reference/design status.

## Success criterion

At any moment the repository should make it possible to answer three separate questions precisely:

1. What runtime behavior has actually been verified?
2. What executable runtime work exists but still needs validation?
3. What architecture has only been designed/documented for future implementation?

This file records that separation for the current milestone.
