# Spectra Science — Test Strategy and Checkpoint Discipline

This document defines how Spectra should validate scientific correctness, capability composition, numerical providers, presentation, backends, schemas, plugins, and product workflows without making every small edit require every expensive environment.

## Principle

Use layered validation.

```text
static/import checks
    -> focused unit/analytical tests
    -> domain/capability integration
    -> full plain-Python suite
    -> native/provider/backend smoke when affected
    -> stress/performance qualification when relevant
```

Do not rerun expensive GPU/Blender/HPC validation for documentation-only or unrelated semantic changes.

## Test layers

### Layer 0 — syntax/import/static boundary

Examples:

```text
python -m compileall spectra
plain Python imports without Blender
no renderer SDK import leaks into Core/domains
no missing public imports
```

Purpose: catch cheap structural failures first.

## Layer 1 — semantic unit tests

Test immutable scientific contracts:

- validation;
- units;
- shape constraints;
- analytical formulas;
- simple field/tensor operations;
- known identities.

Prefer small deterministic cases.

## Layer 2 — capability/domain tests

Validate:

- provider capability published;
- dependency versions;
- arbitrary registration order;
- transactional rollback;
- auto-discovery;
- catalog provider graph;
- capability-driven loading.

A semantic type used as `DomainDependency` must also be provided as a capability.

## Layer 3 — numerical reference tests

Use canonical analytical cases from `CANONICAL_REFERENCE_CASES.md`.

Examples:

```text
ODE exponential growth
harmonic oscillator
constant diffusion state
manufactured Poisson solution
uniform heat source
rigid elastodynamic translation
constant quantum state
```

Check numerical error/invariants, not visual appearance only.

## Layer 4 — solver interchangeability

For every provider implementing a stable role, test:

```text
same problem contract
selection by ID
selection by requirements/policy
problem compatibility
provenance
fallback
result parity/tolerance
```

A faster provider must not require scientific-domain code changes.

## Layer 5 — convergence/stability

Where meaningful:

- observed order;
- refinement trend;
- conservation drift;
- CFL/diffusion diagnostics;
- divergence/continuity residuals.

Fixed-step convergence studies should reject adaptive methods unless using a dedicated adaptive convergence methodology.

## Layer 6 — experiment/reproducibility

Test:

- deterministic case IDs;
- batched grouping;
- failure recording;
- solver comparison;
- sensitivity;
- uncertainty;
- calibration;
- Pareto/ranking;
- environment fingerprint;
- artifact JSON round-trip;
- per-case numerical traces.

## Layer 7 — Scene/view tests

Renderer-neutral checks:

- correct primitive types;
- stable IDs;
- expected topology/count;
- Timeline tracks;
- explicit views preserve semantics;
- display sampling separate from solver resolution.

Use MemoryBackend where helpful.

## Layer 8 — presentation tests

Once presentation runtime exists, plain-Python tests should validate:

- preset semantic contracts;
- deterministic resource IDs;
- camera fitting based on bounds;
- color scale/legend consistency;
- axes/unit metadata;
- presentation composition does not alter science;
- preset switch diff behavior.

These do not require Blender.

## Layer 9 — native Blender tests

Run only when:

- Blender backend changes;
- Scene primitive behavior changes materially;
- presentation Blender mapping changes;
- native animation/ownership lifecycle is affected.

Validate:

```text
import boundary
static create
animated geometry
object/datablock identity
cleanup
batching
frame leak
presentation resources when implemented
```

Use `BLENDER_PREMIUM_ACCEPTANCE.md` for premium phases.

## Layer 10 — native CPU/GPU provider tests

Run when provider/buffer/selection code changes.

Validate:

- canonical reference parity;
- precision;
- convergence;
- problem compatibility;
- provenance;
- resource lifecycle;
- fallback;
- batch behavior.

GPU validation should measure transfer separately from kernel.

## Layer 11 — stress/performance

Do not turn ordinary unit tests into flaky performance assertions.

Dedicated stress/benchmark runs cover:

- 100+ frame scrub;
- repeated create/destroy;
- large PointCloud/VectorGlyphSet;
- large grid kernels;
- long solver histories;
- batch experiments;
- memory/VRAM;
- project open/cache behavior.

Performance results are environment-specific.

## Layer 12 — schema compatibility

For persistent formats keep fixtures for historical versions.

Test:

```text
old fixture -> current reader
current writer -> current reader
migration semantic equivalence
unknown future version rejection
fingerprint/integrity checks where applicable
```

## Layer 13 — plugin contract

When external plugin runtime exists:

- compatible plugin loads;
- incompatible rejected before side effects;
- disabled plugin absent;
- missing project plugin diagnostic;
- provider conflict deterministic;
- registration rollback;
- uninstall/absence does not break base engine.

## Layer 14 — project workflow

Once project runtime exists, test invalidation:

```text
physical parameter change -> result stale
solver policy change -> result stale
view change -> result remains current
presentation change -> result remains current
renderer change -> science remains current
```

This is essential product correctness.

## Layer 15 — headless/CLI

Test command contracts independently from interactive UI:

```text
validate
solve
experiment
view
present
export
inspect
```

Structured JSON output and exit codes should be stable where public.

## Layer 16 — security/trust

Validate safe failures:

- untrusted project cannot auto-install plugin;
- unsafe serialization rejected;
- path traversal blocked in archives;
- remote resource policy honored;
- secrets not serialized to project/provenance;
- unapproved native provider not loaded.

## Test naming

Prefer tests that describe contract:

```text
test_scalar_pde3d_uses_current_first_order_solver
test_presentation_change_does_not_invalidate_result
test_plugin_registration_rolls_back_on_capability_conflict
```

Avoid vague names such as `test_feature_2`.

## Analytical tests vs snapshot tests

Use analytical assertions for scientific correctness.

Visual/Scene snapshots can help detect structural regressions but must not replace numerical assertions.

A pretty image is not proof the physics is correct.

## Tolerances

Numerical tolerances must be tied to:

- algorithm;
- precision;
- grid/step;
- reference case.

Do not use one global `1e-6` for every numerical test.

## Determinism

Tests should be deterministic by default.

If randomness is scientifically needed:

- explicit seed;
- recorded sampling policy;
- tolerance/statistical contract.

Current uncertainty framework prefers deterministic weighted scenarios where possible.

## Checkpoint policy

After a cross-cutting runtime change:

```text
1. targeted tests during development
2. compileall
3. full pytest
4. relevant native/backend/provider smoke
5. record final commit/test count
6. continue
```

Do not stack another major foundational refactor before establishing a green checkpoint unless there is a deliberate reason.

## Current checkpoint history

Recorded important milestone:

```text
acb9e056326177fac49cc57b202ca80cca5090a7
compileall PASS
224 pytest passed
Blender 5.2 native targeted smoke PASS
```

Current `main` has a large post-baseline numerical/experiments runtime batch plus documentation/spec commits and still requires the next full local validation before inheriting a new green claim.

## Documentation-only changes

Documentation/specification-only commits do not require full runtime revalidation merely because the commit SHA changed.

They should still be reviewed for stale/incorrect claims.

The next runtime validation should test the runtime delta, while documentation commits can remain on the same branch.

## Agent/local-validator report format

Useful final report:

```text
final SHA
compileall PASS/FAIL
full pytest count
initial failures
root fixes
DomainCatalog/domain/provider count
numerical/provider status
experiments/reproducibility status
native backend/provider smoke if relevant
repo clean/sync status
remaining blockers
```

## Failure triage

When many tests fail, first look for root causes:

```text
missing provider capability
version mismatch
import cycle
shared API signature change
wrong unit conversion
catalog auto-discovery failure
schema constructor change
```

Do not patch dozens of expectations before identifying a shared regression.

## Test changes

Change a test only when:

- the contract intentionally changed;
- old expectation is stale/wrong;
- new scientific behavior is explicitly documented.

Do not weaken assertions solely to make suite green.

## Backend full rebuild fallback

Tests should not force an incremental backend to rebuild everything just because it is simpler to satisfy identity-insensitive assertions.

Stable identity is itself a contract for performance-oriented paths.

## Benchmark promotion

Before making a provider/default performance claim, pair timing with correctness.

Minimum report:

```text
reference error
candidate error
workload
setup/transfer/kernel/materialization timing
memory where known
```

## Success criterion

Spectra should be able to evolve rapidly while every important layer has an appropriate validation depth, expensive environments are used only when relevant, and green checkpoint claims remain tied to recorded commits rather than assumed from previous history.
