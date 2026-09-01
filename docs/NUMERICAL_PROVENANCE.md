# Spectra Science — Numerical Provenance

Spectra separates scientific semantics from numerical implementation details, but scientific results still need to record **how they were computed**.

The provenance layer is deliberately additive. Ordinary solver capabilities may continue returning their semantic solution types, while tracked capabilities return the same result plus numerical execution metadata.

## Why provenance exists

Two scientifically identical problem definitions may be executed with different:

- numerical methods;
- solver implementations;
- fixed/adaptive stepping;
- precision;
- CPU/GPU/external backends;
- step counts/tolerances;
- solver policies.

A result should therefore be able to say more than "the PDE solver ran".

The intended separation is:

```text
scientific problem semantics
        ↓
stable solver role
        ↓
selected implementation
        ↓
numerical execution
        ↓
solution + NumericalRunRecord
```

## Public patterns

Legacy/direct reference capabilities may expose:

```text
<solver>
<solver>.method
<solver>.tracked
```

Examples include:

```text
ode.solve_rk4
ode.solve_rk4.method
ode.solve_rk4.tracked
```

The preferred interchangeable execution path uses stable roles/dispatch:

```text
ode.solver_role.first_order
ode.solve_first_order
ode.solve_first_order.tracked
ode.solve_first_order_selected
ode.solve_first_order_selected.tracked
```

Higher-level scientific domains should normally depend on the stable role-dispatch capability rather than naming a concrete method such as RK4.

## Core numerical records

`spectra.numerics` defines renderer- and domain-neutral numerical metadata.

### `NumericalMethodDescriptor`

Describes one numerical method implementation, including conceptually:

- method ID;
- family;
- implementation identifier;
- formal order when meaningful;
- adaptive/fixed flag;
- reference-implementation flag;
- notes.

Examples:

```text
rk4.fixed
heun.fixed
rk45.dormand_prince
```

### `NumericalPipelineDescriptor`

Describes an ordered composition of numerical stages.

For a method-of-lines PDE the pipeline may be:

```text
method-of-lines.scalar3d
    -> selected first-order time integrator
```

The second stage must reflect the **actual runtime-selected implementation**, not a hardcoded RK4 label.

### `NumericalExecutionDescriptor`

Describes execution characteristics separately from scientific meaning:

- execution kind: `python`, `cpu`, `gpu`, `external`;
- backend identifier;
- precision;
- optional device;
- in-place support;
- batched support.

Changing execution backend does not by itself change scientific semantics.

### `NumericalRunRecord`

A tracked run records, where available:

- method or composed pipeline;
- actual start time;
- actual end time;
- accepted/integration step count;
- requested step count or initial step-count hint;
- state size;
- semantic tags;
- stable solver role;
- selected implementation ID;
- execution kind/backend/precision/device metadata.

The run record must describe what actually happened, not only what the caller requested.

### `TrackedNumericalResult[T]`

Carries:

```text
result: T
run: NumericalRunRecord
```

The semantic result remains usable independently from the provenance wrapper.

## Fixed-step semantics

For fixed-step methods such as reference RK4/Heun:

```text
requested_steps == accepted_steps
```

and a meaningful uniform fixed step size can be derived:

```text
(end_time - start_time) / accepted_steps
```

For these runs, `fixed_step_size` is valid.

## Adaptive-step semantics

For adaptive methods such as the reference Dormand–Prince/RK45 provider, the caller's `steps` argument is an **initial step-size/count hint**, not a promise that the solver will take exactly that many accepted steps.

Therefore:

```text
requested_steps = caller hint
accepted steps = len(solution.times) - 1
```

These values may differ.

An adaptive run does not have one scientifically meaningful global fixed step size, so a fixed-step-size property must not pretend otherwise.

Tolerance/control metadata can be added to provenance as the adaptive execution contract matures.

## Actual returned interval

Tracked provenance should derive the authoritative integration interval from the returned solution history where appropriate.

A native/adaptive implementation must not claim it reached a requested end time if its returned solution does not actually end there.

Likewise, a higher-level PDE tracked result should propagate the true lower-level solver interval rather than reconstructing it from caller arguments only.

## Runtime solver selection

A stable role may have multiple loaded implementations:

```text
ode.first_order
    -> rk4.reference
    -> heun.reference
    -> rk45.reference
    -> future native_cpu / gpu / external providers
```

Selection may depend on:

- execution requirements;
- precision;
- minimum method order;
- adaptive/fixed requirement;
- tags;
- problem compatibility;
- priority;
- active ordered fallback policy;
- exact explicit implementation ID.

Tracked provenance must identify the implementation that was actually selected.

It is insufficient to record only the stable role.

## Solver policies and reproducibility

A scientific environment may contain the same solver inventory but use different active selection policies.

For example:

```text
policy A: GPU non-reference -> CPU non-reference -> default
policy B: default reference only
```

These environments are not execution-equivalent.

Therefore reproducibility snapshots include active solver policies in the environment fingerprint in addition to domains, capabilities, implementations, execution metadata, and defaults.

## PDE provenance

A high-level tracked PDE solve should compose its spatial/discretization stage with the **actual tracked time-integration method**.

Example:

```text
method-of-lines.scalar3d
    +
rk45.dormand_prince
```

or:

```text
method-of-lines.scalar3d
    +
native_cpu.rk4
```

The PDE layer should preserve:

- accepted step count;
- requested step hint;
- solver role;
- selected implementation;
- execution backend/precision.

This is required so replacing Python reference execution with native/GPU execution does not produce misleading provenance.

## Scientific pipelines beyond one solver

A multiphysics operation may invoke several tracked numerical runs.

Examples:

```text
reaction-diffusion solve
    -> heat solve
    -> elastodynamics solve
```

or:

```text
Maxwell field solve
    -> charged-particle trajectory
```

The experiment tracing layer therefore supports **multiple numerical run records per experiment case** rather than forcing one case = one solver assumption.

## Experiment tracing

Tracked experiment execution can preserve, per case:

- case ID and parameters;
- metrics;
- zero/one/many numerical run summaries;
- method/pipeline identity;
- solver role/implementation;
- execution backend/precision;
- requested/accepted steps;
- errors.

This allows one experiment artifact to answer questions such as:

> Which implementation produced case 0042?

or:

> Did this parameter sweep mix RK4 reference and a GPU provider because of problem-compatibility fallback?

## Durable artifacts

Schema-versioned experiment artifacts may serialize numerical run summaries along with:

- parameter axes;
- case parameters;
- metrics/units;
- failures;
- scientific environment snapshot;
- environment fingerprint;
- user/application metadata.

Arbitrary runtime solver output is intentionally not required to be serialized into the artifact summary.

This keeps durable experiment metadata separate from potentially huge/native runtime objects.

## Convergence methodology

Fixed-step convergence studies refine explicit fixed step counts:

```text
8 -> 16 -> 32 -> 64
```

and estimate observed order from error ratios.

An adaptive solver must not be silently passed through the same API because changing the initial step hint is not equivalent to fixed-step grid refinement.

Adaptive convergence/tolerance studies should use a separate methodology when implemented.

## Reference vs production

Provenance does not promote a reference solver to production quality.

A record such as:

```text
implementation = spectra.reference.rk4
```

is useful precisely because it makes the reference implementation explicit.

Reference CFD/FDTD/FEA/PDE solvers remain reference implementations until numerical validation/performance criteria justify a stronger claim.

## Native/GPU providers

Native/GPU implementations should publish the same provenance dimensions as reference solvers plus relevant execution metadata.

At minimum:

- stable role;
- unique implementation ID;
- method/pipeline descriptor;
- execution kind/backend;
- precision;
- device when meaningful;
- accepted/requested step semantics;
- problem compatibility;
- provider domain.

See:

- `NATIVE_NUMERICAL_BACKENDS.md`
- `NUMERICAL_BUFFERS.md`
- `NUMERICAL_BACKEND_VALIDATION.md`

## What provenance does not replace

Scientific reproducibility may eventually also need:

- source-control revision;
- external input dataset hashes;
- plugin/package versions;
- native library build/ABI IDs;
- compiler/runtime versions;
- hardware details;
- random seeds where stochastic algorithms are used.

The current numerical run/environment records are an extensible foundation, not a claim that every reproducibility dimension is already captured.

## Design constraints

Do not:

- change a semantic solution type only to expose implementation trivia;
- hardcode RK4 into high-level provenance after runtime solver interchangeability exists;
- claim requested steps are accepted steps for adaptive solvers;
- invent a fixed step size for adaptive histories;
- lose the selected implementation ID behind a stable role name;
- hide execution policy differences from environment fingerprints;
- make Blender/render metadata part of numerical provenance;
- present reference solvers as industrial-grade merely because they are tracked.

## Success criterion

Given a tracked scientific result, Spectra should be able to explain both:

```text
WHAT scientific problem/result this is
```

through domain semantics, and:

```text
HOW this numerical result was produced
```

through method/pipeline, implementation, execution, and run provenance — without coupling either layer to the renderer.
