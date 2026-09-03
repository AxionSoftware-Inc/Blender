# Spectra Science — Diagnostics, Warnings, and Errors

This document defines how Spectra should report problems across scientific semantics, capability loading, numerical execution, experiments, presentation, plugins, and renderer backends.

The objective is to make failures actionable without leaking backend internals into scientific APIs or hiding scientific invalidity behind generic exceptions.

## Principles

1. Fail early for invalid scientific semantics.
2. Distinguish user/input errors from unsupported capability from numerical failure from backend failure.
3. Do not silently change scientific meaning to make execution succeed.
4. Preserve the last valid result when a new attempt fails where product workflow allows it.
5. Diagnostics should be machine-readable enough for UI/CLI/AI surfaces and human-readable enough for developers/users.
6. Renderer/backend failures must not be misreported as scientific-model errors.

## Diagnostic categories

Recommended top-level categories:

```text
validation
capability
numerical
convergence
stability
resource
plugin
presentation
backend
serialization
reproducibility
```

These are conceptual categories; exact runtime types can be implemented later.

## Severity

A diagnostic should distinguish:

```text
info
warning
error
fatal
```

### Info

Useful context that does not imply a problem.

Examples:

- selected solver implementation;
- fallback selected by policy;
- presentation display decimation active.

### Warning

Computation/presentation can proceed, but interpretation or quality may be limited.

Examples:

- reference solver used outside recommended size range;
- CFL diagnostic near stability limit;
- display color range clips outliers;
- backend lacks requested premium effect and uses a documented fallback.

### Error

Requested operation cannot produce a valid result.

Examples:

- unit mismatch;
- unsupported solver/problem combination;
- invalid boundary configuration;
- plugin capability conflict;
- renderer cannot materialize required primitive semantics.

### Fatal

Session/process/subsystem cannot safely continue.

Use sparingly.

Examples might include corrupted persistent state that cannot be parsed safely or a native provider violating its declared memory/lifecycle contract.

## Scientific validation errors

Scientific semantic constructors and problem definitions should reject invalid state before numerical execution.

Examples:

```text
quantity dimension mismatch
grid/state length mismatch
non-finite input
negative mass where prohibited
invalid boundary mode
invalid time interval
empty required state
```

Messages should identify:

- object/parameter;
- expected contract;
- actual value/dimension/shape;
- relevant unit where applicable.

Bad:

> invalid value

Better:

> `charge_density` must have charge/volume dimension; received kg/m^3.

## Capability errors

Capability loading/selection diagnostics should distinguish:

### Missing provider

No loaded/discoverable domain provides the required capability.

### Version mismatch

Provider exists but does not satisfy required minimum contract version.

### Dependency cycle

Provider graph cannot be resolved.

### Provider conflict

More than one provider claims a capability under a model that requires uniqueness.

### Registration rollback

A domain failed during registration and all mutations were reverted.

Diagnostics should include the dependency/provider chain where practical.

## Numerical selection errors

Solver selection should explain why candidates were rejected.

Useful rejection reasons:

```text
wrong execution kind
unsupported precision
method order too low
adaptive/fixed mismatch
missing required tag
problem compatibility predicate false
provider unavailable/not loaded
```

Example advanced diagnostic:

```text
No solver satisfies role `ode.first_order` for problem `stiff_decay`.
Candidates:
- rk4.reference: rejected, adaptive required
- heun.reference: rejected, adaptive required
- rk45.reference: rejected, problem compatibility predicate false
```

Normal UI may summarize this while an expandable detail panel shows the full reasoning.

## Numerical runtime errors

Numerical execution may fail because of:

- non-finite derivative/state;
- linear solve failure;
- iteration limit;
- invalid timestep;
- convergence failure;
- provider/native error;
- resource exhaustion.

Tracked numerical execution should preserve enough context to identify:

```text
solver role
implementation id
method id
start/end time
requested/accepted steps or tolerance
state size
problem name
execution backend/precision
```

Do not catch all numerical exceptions and replace them with a generic "simulation failed" without retaining the original diagnostic context.

## Stability diagnostics

Stability checks are often warnings/analysis outputs rather than hard errors.

Examples:

```text
CFL number
diffusion number
divergence residual
energy drift
continuity residual
```

A reference solver may permit the user to proceed despite a warning, depending on the contract.

The diagnostic should state whether a threshold is:

- mathematically required by the method;
- conservative heuristic;
- project policy;
- user-configured limit.

## Convergence diagnostics

Convergence studies should distinguish:

- observed order unavailable because errors are zero;
- observed order below expected;
- adaptive method passed to fixed-step study;
- refinement sequence invalid;
- reference solution/tolerance unavailable.

A failed convergence expectation should not automatically mean the solver is universally wrong; it means the declared case/expected-order contract was not met.

## Experiment errors

Parameter sweeps support at least two behaviors:

```text
raise
record failure
```

Recorded case failure should retain:

```text
case id
parameter values
error category/message
numerical trace if execution began
```

One failed case should not erase successful cases in `record` mode.

Calibration/uncertainty/Pareto analyses should clearly state whether failed cases are excluded or make the analysis invalid.

## Presentation warnings

Presentation warnings must never be confused with scientific warnings.

Examples:

- requested cinematic volumetrics unsupported by backend;
- legend overlaps primary content and fallback placement was used;
- display glyph sampling reduced for performance;
- quantitative color range clipped at declared percentile;
- screen-space labels unsupported, world-space labels used.

These warnings do not imply the numerical result changed.

## Backend errors

Backend failures should identify native operation without leaking it into scientific semantics.

Examples:

```text
failed to create native mesh for Surface
failed to update curve datablock for Polyline
renderer capability unsupported
native resource allocation failed
presentation compositor unavailable
```

Backend diagnostics may include native exception details for developer mode.

A backend must not silently substitute a scientifically different representation merely because native materialization failed.

## Resource/ownership errors

Examples:

- duplicate native mapping for one Spectra ID;
- cleanup attempted on resource owned by another project/session;
- unexpected native object missing during incremental update;
- leaked/undestroyed session resource detected by validation.

These are architecture/runtime integrity issues and should be visible in development/stress validation.

## Plugin errors

External plugin diagnostics should distinguish:

```text
plugin not compatible with Spectra version
plugin import failure
plugin descriptor invalid
capability conflict
native library missing
optional dependency unavailable
plugin disabled by user/policy
```

A broken optional plugin must not make base Spectra unusable unless the active project explicitly depends on that plugin.

## Serialization errors

Persistent formats should reject:

- unknown schema when no compatibility path exists;
- unsupported future version;
- malformed required field;
- fingerprint mismatch where integrity is checked;
- invalid unit encoding;
- invalid reference/resource ID.

Do not partially accept corrupt scientific state and silently fill missing values with guesses.

## Reproducibility diagnostics

A product may compare the environment recorded with a result/project against the current environment.

Useful outcomes:

```text
exact match
compatible but different implementation
missing required domain/capability
solver policy changed
plugin missing
presentation-only difference
source-control/environment metadata unavailable
```

A mismatch should be described precisely instead of simply saying "not reproducible".

## Structured diagnostic concept

A future generic diagnostic record may contain:

```text
code
category
severity
message
component
operation
subject_id
context key/value pairs
cause chain
suggested action
```

Example conceptual code:

```text
NUMERICAL_SOLVER_NOT_FOUND
UNIT_DIMENSION_MISMATCH
DOMAIN_PROVIDER_CONFLICT
BACKEND_RESOURCE_LEAK
PRESENTATION_FALLBACK_USED
```

Codes should be stable enough for UI filtering/logging; messages can evolve.

## Suggested actions

Where an actionable safe remedy exists, diagnostics may provide one.

Examples:

```text
Load capability provider `differential_equations.adaptive_reference`.
Select a fixed-step solver for this convergence study.
Use a charge-density unit such as C/m^3.
Reduce requested presentation effect or choose a backend supporting volumetrics.
```

Do not suggest scientifically unsafe automatic corrections.

## User vs developer detail

A future UI should support levels:

### User summary

Short, domain-relevant message.

### Technical detail

Capability IDs, solver/provider IDs, units, state sizes, backend operation.

### Developer trace

Native exception/call context where appropriate.

This avoids exposing Blender/Python internals to normal users while preserving debugging value.

## Logging

Logging should be supplemental to structured errors, not the only place important failure information exists.

Potential channels:

```text
project log
numerical log
backend log
plugin log
validation report
```

Do not rely on `print()` from domain modules as the primary error/reporting interface.

## AI surface behavior

An AI authoring layer should receive structured diagnostics and explain them, but must not bypass them.

If the engine says a unit is invalid or a solver is unsupported, AI should modify the project/command explicitly rather than mutating hidden runtime state to force execution.

## Success criterion

When an operation fails, a user or agent should be able to answer:

```text
Was the scientific model invalid?
Was a required capability missing?
Was no compatible solver available?
Did numerical execution fail?
Was the result scientifically suspicious but still produced?
Did presentation degrade only visually?
Did the renderer/backend fail?
```

without guessing from a generic stack trace.
