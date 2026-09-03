# Spectra Science — Remote Execution and Worker Contract

This document defines how future local workers, remote servers, HPC clusters, or cloud GPU jobs should execute Spectra numerical work without becoming separate scientific engines.

## Goal

The same scientific problem and numerical role should be executable through:

```text
local Python
local native CPU
local GPU
remote workstation
cluster/HPC worker
cloud batch job
```

without changing scientific-domain semantics.

Conceptual boundary:

```text
Project/model semantics
        ↓
Execution request
        ↓
worker transport
        ↓
Spectra-compatible worker
        ↓
solver role/provider
        ↓
semantic result + provenance
```

## Worker responsibility

A worker may own:

- numerical provider runtime;
- CPU/GPU/native libraries;
- temporary execution buffers;
- resource staging;
- progress reporting;
- result serialization;
- logs/diagnostics.

A worker must not invent scientific semantics missing from the request.

## Execution request

A future execution request should identify conceptually:

```text
request id
scientific model/problem payload or reference
required capabilities
solver role
solver requirements/policy
execution precision
numerical parameters/tolerances
input resource references/hashes
expected output contract
project/model revision
```

The request should be renderer-independent.

Do not send Blender objects as scientific inputs to an HPC worker.

## Provider selection

Selection may happen:

- before dispatch, when the client knows worker capabilities;
- on the worker, using declared solver requirements/policy;
- through negotiated constraints.

Whichever model is used, the final selected implementation must be recorded in provenance.

## Worker capability profile

A worker may advertise:

```text
Spectra API/version
loaded domain/capability inventory
solver roles/implementations
CPU architecture
GPU/device type
supported precision
memory limits
native ABI versions
optional plugins
maximum problem classes/sizes
```

This resembles renderer capability negotiation but is for numerical execution.

## Compatibility check

Before a job begins, verify at minimum:

```text
required domain/capability versions
problem serialization compatibility
solver role availability
precision support
plugin availability
resource availability
native ABI compatibility where relevant
```

Fail before expensive execution if requirements cannot be met.

## Scientific environment snapshot

The worker should return or contribute to a reproducibility snapshot including:

```text
loaded domains/capabilities
selected solver implementation
method descriptor
execution backend/device/precision
active solver policy if relevant
worker/runtime version
```

Future provenance may also include:

- OS;
- CPU/GPU model;
- driver/runtime versions;
- native library versions;
- compiler/build identifiers.

## Job lifecycle

Conceptual states:

```text
queued
staging
validating
running
finalizing
succeeded
failed
cancelled
```

A product UI may expose these states, but scientific solver APIs remain synchronous contracts inside a worker.

## Progress

Progress is product/runtime metadata, not scientific state.

Possible progress information:

```text
stage
fraction if meaningful
accepted steps / current time
iteration count
batch index
resource staging progress
```

Do not fabricate a smooth percentage when the algorithm has no meaningful progress estimate.

## Cancellation

Cancellation should be cooperative where possible.

A worker may check cancellation between:

- timesteps;
- nonlinear iterations;
- batches;
- major solver phases.

Cancellation should produce a distinct status, not masquerade as numerical failure.

Partial numerical results should only be published if the solver contract explicitly defines them as valid/interpretable.

## Retry

Retries are safe only for failures known to be transient.

Potentially retryable:

- worker lost before execution started;
- staging/network timeout;
- temporary scheduler failure.

Do not blindly retry:

- unit validation errors;
- unsupported solver/problem combinations;
- deterministic convergence failures;
- out-of-domain scientific inputs.

## Resource staging

Large external resources should be referenced by logical ID/hash.

A worker may:

```text
reuse cached resource by hash
upload missing resource
mount shared storage
stream required subset
```

The execution request should not duplicate multi-gigabyte arrays in JSON.

See `DATA_INGESTION_AND_RESOURCES.md`.

## Result transport

Results may contain:

```text
small semantic metadata
numerical arrays/history
metrics/diagnostics
experiment artifacts
provenance
external large-result resource references
```

Large results may use chunked/binary storage referenced by a semantic envelope.

The transport format must not force renderer-specific representation.

## Result publication

A remote result should become visible to the project only after validation/commit of the complete result contract.

Avoid exposing half-written result resources as current project truth.

A product may retain failed-attempt diagnostics separately.

## Stale jobs

A project can change while a remote job is running.

Therefore an execution request should include a model/revision/fingerprint.

When result returns:

```text
if result revision == current model revision
    mark current
else
    store as historical/stale result
```

Do not overwrite a newer model's result silently.

## Multi-stage workflows

A workflow may chain:

```text
Maxwell solve
   -> Joule heat field
   -> heat solve
   -> thermoelastic solve
```

Possible scheduling strategies:

- one worker executes the whole coupled pipeline;
- stages execute on different workers and exchange semantic results/resources.

The coupling semantics remain the same either way.

## Experiment distribution

Parameter sweeps are naturally distributable.

The experiment layer already defines deterministic case IDs and batching concepts.

Future scheduler mapping:

```text
ParameterCase IDs
    -> worker batches
    -> per-case outputs/traces
    -> deterministic ExperimentResult assembly
```

Failure recording must preserve case identity.

## Determinism

Remote execution should not claim bitwise reproducibility unless the provider/runtime guarantees it.

Reproducibility may instead mean:

- same scientific model;
- same method/provider/precision;
- same resource inputs;
- results within declared numerical tolerance.

GPU/native reductions may differ slightly in floating-point order.

## Security/authentication

Worker communication must eventually address:

- authentication;
- authorization;
- transport security;
- project/resource access boundaries;
- plugin/native code trust;
- secrets handling.

Do not embed cloud/API secrets into scientific project documents.

## Sandboxing

A shared worker should not execute arbitrary Python imported from an untrusted project by default.

Allowed execution should come from installed/approved Spectra domains/plugins/provider packages.

Future plugin trust policy is described in `TRUST_AND_SECURITY_MODEL.md`.

## Worker isolation

For multi-user/shared infrastructure consider:

- process/container isolation;
- filesystem sandboxing;
- GPU memory limits;
- CPU/RAM quotas;
- execution time limits;
- per-project resource namespaces.

These are deployment/product concerns but influence safe worker design.

## Failure diagnostics

A worker should return structured diagnostics rather than only raw logs.

Examples:

```text
capability unavailable
resource hash missing
solver rejected problem
native provider error
out of memory
job cancelled
numerical convergence failure
```

See `DIAGNOSTICS_AND_ERRORS.md`.

## Renderer separation

Remote numerical workers should not require Blender.

A render worker is a different role:

```text
scientific result/Scene
    -> render worker
```

A combined worker may host both, but the contracts should remain distinct.

## Scheduling hints

Execution requests may eventually provide non-scientific resource hints:

```text
prefer GPU
minimum VRAM
minimum RAM
expected runtime class
batch-friendly
latency-sensitive
```

These hints must not alter scientific meaning silently.

## Cost-aware policies

A product may select between local/remote providers based on:

- latency;
- cost;
- data transfer;
- resource availability;
- privacy policy.

The resulting selected execution environment should be captured in provenance where relevant.

## Offline behavior

Base Spectra should remain usable locally without a remote service.

Remote execution should be an execution provider/product layer, not a requirement for the scientific semantic engine.

## Success criterion

A heavy Spectra simulation should be able to move from a user's laptop to a remote CPU/GPU/HPC worker while keeping the same scientific model, capability contracts, solver roles, result semantics, experiment case identities, and downstream Blender/WebGPU presentation pipeline.
