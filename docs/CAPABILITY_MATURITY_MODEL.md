# Spectra Science — Capability Maturity and Verification Model

This document defines a shared vocabulary for describing how mature a Spectra capability, solver, backend, presentation feature, or module actually is.

The goal is to prevent statements such as "supported" or "works" from hiding important differences between a design contract, implemented reference code, locally verified behavior, and production-ready functionality.

## Two independent dimensions

Spectra should distinguish:

1. **implementation maturity** — how complete/robust the feature is;
2. **verification status** — what has actually been tested and where.

A feature can be implemented but unverified, or highly verified but still intentionally a reference implementation rather than industrial-grade.

## Implementation maturity levels

### `design`

Architecture/specification exists, but runtime implementation is intentionally absent or incomplete.

Examples today may include:

- external plugin entry-point discovery;
- full premium presentation runtime;
- public `spectra.sdk` facade;
- project document runtime;
- native/GPU numerical providers.

A design-level feature must never be presented as executable functionality.

### `prototype`

Runtime exists primarily to prove an API or architecture.

Characteristics:

- limited cases;
- incomplete error handling;
- performance not representative;
- API may still change materially.

### `reference`

Deterministic, correctness-oriented implementation intended to define/validate a scientific or numerical contract.

Characteristics:

- tests/analytical cases expected;
- performance secondary;
- algorithm may be deliberately simple;
- not automatically suitable for industrial workloads.

Examples:

```text
reference RK4
reference Heun
reference Poisson/PDE/CFD/Maxwell layers
```

### `experimental`

Usable runtime implementation beyond a minimal reference, but broader robustness/performance/compatibility has not been established.

May be appropriate for advanced users who understand limitations.

### `beta`

Feature contract is relatively stable and has meaningful real-world validation, but compatibility/performance/edge cases are still being expanded.

### `production`

Feature has explicit supported scope, strong validation, failure behavior, lifecycle/resource handling, documentation, and compatibility guarantees appropriate to its stated use.

`production` does not mean scientifically universal. A production solver can still support a narrow class of problems.

## Verification levels

### `not_run`

No current execution evidence for the implementation/version under discussion.

### `static_reviewed`

Architecture/signatures/contracts reviewed, but no runtime test result is claimed.

### `targeted_pass`

Relevant focused tests/smokes passed.

Examples:

```text
one analytical solver case
one Blender native animation smoke
one plugin load scenario
```

### `suite_pass`

Full relevant automated suite passed at a recorded commit.

### `native_pass`

Relevant native/external runtime passed.

Examples:

- Blender embedded Python;
- native CPU library;
- CUDA/Metal/WebGPU provider;
- remote/HPC worker.

### `stress_pass`

Repeated/large workload, lifecycle, memory, leak, or long-running behavior passed defined stress criteria.

### `release_qualified`

The documented supported scope passed the release qualification matrix for its maturity level.

## Status record concept

A future machine-readable status record may look conceptually like:

```text
component_id
component_version
maturity
verification_level
verified_commit
verified_environment
supported_scope
known_limitations
reference_cases
benchmark_context
last_verified_at
```

Do not derive maturity automatically from test count alone.

## Example status interpretations

### Blender incremental backend

At the recorded `acb9e056...` milestone:

```text
implementation maturity: experimental/reference backend
verification: native_pass + targeted stress checks
```

It has real Blender 5.2 validation, stable identity, dense batching, cleanup, and frame-leak checks, but broader save/reload, long sessions, many scene types, and production UX are not yet fully qualified.

### Reference incompressible CFD

```text
implementation maturity: reference
verification: suite_pass at a recorded baseline when included
```

This means the architecture and numerical reference behavior are useful. It does not mean industrial turbulence/meshing/robustness equivalent to commercial CFD software.

### Premium presentation system today

```text
implementation maturity: design
verification: static_reviewed documentation only
```

Do not report cinematic presets/legends/Blender premium mapping as already implemented until runtime phases land and are tested.

### Solver-role/experiment batch before next local validation

```text
implementation maturity: reference/experimental architecture
verification: not yet full suite_pass on current head
```

Individual code may have targeted reasoning/review, but the current `main` must not inherit the older 224-pass claim automatically.

## Scientific fidelity vs software maturity

These are also distinct.

A stable software implementation of a simplified physical model may be production-quality software for that simplified model while not representing advanced real-world physics.

Therefore component documentation should state both:

```text
software maturity
scientific/model scope
```

Example:

```text
Heat conduction 3D
software maturity: reference
model scope: homogeneous/reference finite-difference conduction, not general industrial thermal FEM
```

## Numerical provider promotion

A faster provider should progress conceptually:

```text
design
  -> prototype
  -> reference parity
  -> experimental
  -> beta
  -> production within declared scope
```

Promotion criteria may include:

- canonical reference cases;
- convergence behavior;
- precision matrix;
- provenance correctness;
- problem compatibility;
- memory/resource safety;
- performance benefit;
- fallback behavior.

Performance alone does not promote maturity.

## Presentation/backend promotion

A renderer feature should not be called production merely because a single render looks good.

Promotion requires relevant gates from `BLENDER_PREMIUM_ACCEPTANCE.md`, including:

- deterministic ownership;
- cleanup;
- quantitative color integrity;
- identity/incremental behavior;
- preset switching;
- canonical scenes;
- lifecycle/stress tests.

## Domain/module maturity

Third-party or built-in scientific modules may declare maturity independently.

Useful examples:

```text
physics.optics.geometric: reference
vendor.specialized_plasma: experimental
biology.example_teaching_model: prototype
```

Catalog discovery should not automatically imply endorsement or production status.

## UI behavior

A future product may display compact badges such as:

```text
Reference
Experimental
Beta
Production
```

and separate verification detail:

```text
Verified on Blender 5.2
Full suite passed at commit ...
GPU provider not verified
```

Do not overwhelm normal users with internal details by default, but advanced/analysis mode should make them inspectable.

## Warnings

A product may warn when a user selects:

- a reference solver for a workload beyond documented scope;
- an experimental backend;
- an unverified current-head implementation;
- unsupported precision/problem type;
- a design-only feature exposed accidentally.

Warnings should be specific, not generic fear banners.

## Documentation wording

Preferred:

> Reference 3D incompressible-flow solver with diagnostics.

Avoid:

> Full CFD supported.

Preferred:

> Blender 5.2 native smoke and incremental identity validated at commit X.

Avoid:

> Blender backend is fully production-ready.

Preferred:

> Premium presentation architecture is specified; runtime implementation follows after the current validation milestone.

Avoid:

> Cinematic presentation already works.

## Success criterion

At any moment a developer, agent, UI, or user should be able to distinguish:

```text
specified
implemented
verified
stress-tested
production-qualified
```

without relying on vague statements or inheriting stale validation claims from older commits.
