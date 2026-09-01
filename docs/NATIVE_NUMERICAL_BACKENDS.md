# Spectra Science — Native and GPU Numerical Backend Contract

This document defines the architectural contract for future native CPU, GPU, and external numerical solver providers. It is intentionally backend-neutral: CUDA, Metal, Vulkan compute, WebGPU, C++ SIMD, Rust, remote HPC services, or another execution technology may satisfy the same contract.

## Goal

Scientific domains must remain unchanged when execution moves from the Python reference implementation to a native or GPU implementation.

The intended boundary is:

```text
scientific semantics
        ↓
stable numerical role
        ↓
NumericalSolverRegistry
        ↓
reference Python / native CPU / GPU / external provider
```

A backend provider changes *how* a numerical contract executes, not *what* the scientific problem means.

## Provider responsibilities

A native or GPU solver provider should:

1. live outside Core and outside subject-specific scientific semantics;
2. depend on the stable solver-role capability it implements;
3. expose at least one ordinary discoverable capability so `DomainCatalog` can load it;
4. register a unique implementation ID in `NumericalSolverRegistry`;
5. provide numerical-method metadata;
6. provide execution metadata;
7. define problem compatibility when support is not universal;
8. preserve the role's call and result contract;
9. report enough runtime provenance for experiment tracing;
10. be validated against at least one trusted reference implementation.

A provider must not require physics, chemistry, geometry, or another scientific domain to import CUDA/Metal/WebGPU/native-runtime concepts.

## Stable role versus provider capability

Provider discovery and runtime selection are separate.

Example:

```text
capability: ode.first_order.native_gpu
        ↓
DomainCatalog loads NativeGpuODESolverDomain
        ↓
provider registers:
    role = ode.first_order
    implementation_id = rk45.cuda
        ↓
solver policy selects implementation at runtime
```

The capability identifies the provider domain. The implementation ID identifies one loaded execution implementation.

## Implementation identifiers

Implementation IDs must be stable and descriptive. Suggested form:

```text
<method>.<backend>[.<variant>]
```

Examples:

```text
rk4.reference
rk45.reference
rk4.native_cpu
rk45.cuda
rk45.metal
rk45.webgpu
```

Do not encode transient device IDs, driver versions, or machine names in the implementation ID. Device-specific details belong in execution/run provenance.

## Execution metadata

Every implementation should provide `NumericalExecutionDescriptor` values that truthfully describe the execution path:

- `kind`: `python`, `cpu`, `gpu`, or `external`;
- `backend`: stable backend family identifier;
- `precision`: numerical storage/compute precision;
- optional `device` identifier;
- whether in-place operation is supported;
- whether native batching is supported.

Metadata is part of solver selection and reproducibility. It must not be decorative.

## Problem compatibility

A provider may support only a subset of problems. Examples:

- maximum state size;
- only contiguous scalar state vectors;
- only `float32`;
- only fixed topology/grid shape;
- no Python callback inside the time loop;
- only autonomous systems;
- only specific boundary modes;
- only dense rather than sparse state.

Such constraints belong in the implementation's `supports_problem` predicate or an equivalent provider-side compatibility layer.

Unsupported problems must fail selection cleanly. They must not silently execute an approximation with different semantics.

## Ordered solver policies

Product code should not contain scattered backend checks such as:

```text
if cuda_available: ...
elif metal_available: ...
else: ...
```

Instead configure an ordered `NumericalSolverPolicy`, for example:

```text
1. GPU, non-reference, float32/float64, compatible problem
2. native CPU, non-reference, compatible problem
3. default reference implementation
```

The scientific domain continues calling the stable role-dispatch capability.

## Result compatibility

An interchangeable implementation must return the same semantic result type as other implementations of the role.

For `ode.first_order`, that currently means an `ODESolution` contract with:

- monotonically increasing `times`;
- one state per time;
- stable state dimensionality;
- the requested terminal time reached within the solver contract.

Adaptive implementations may return a variable number of accepted steps. Consumers must not assume `len(times) == requested_steps + 1` unless they explicitly selected a fixed-step method.

## Memory ownership

Native providers must make ownership explicit.

Recommended rules:

- semantic problem objects remain engine-owned immutable intent;
- provider-created device/native buffers are provider-owned;
- returned Spectra semantic results must not depend on a buffer that can disappear after provider cleanup;
- zero-copy views are allowed only behind an explicit lifetime contract;
- no renderer backend owns numerical solver memory by default;
- no numerical backend owns Scene/renderer objects.

This separation prevents Blender/WebGPU renderer lifetimes from becoming solver lifetimes.

## Copy boundaries

A high-performance provider should minimize copies but never hide them.

Potential paths:

```text
Python semantic state
    ↓ one packing copy
native contiguous host buffer
    ↓ optional device upload
GPU device buffer
    ↓ compute
result buffer
    ↓ one semantic materialization or persistent buffer view
Spectra result
```

The first native implementation should prioritize correctness and traceability before zero-copy complexity.

## Precision

Precision is a solver property, not a scientific-domain property.

A provider must advertise actual precision. A `float32` GPU implementation must not report `float64` because the public Python result is converted to Python floats afterward.

Experiments should be able to compare:

```text
reference float64
native CPU float64
GPU float32
GPU float64
```

using identical problem semantics and validation metrics.

## Batched execution

Providers that can process multiple independent problems efficiently should advertise batching.

Batching must preserve deterministic input/output correspondence:

```text
input cases [A, B, C]
        ↓
provider batch
        ↓
outputs [result(A), result(B), result(C)]
```

A provider must never reorder outputs without returning an explicit mapping.

The generic experiment batching contract is the preferred entry point for parameter studies.

## Adaptive solvers

Adaptive implementations must distinguish:

- requested initial step-size/step-count hint;
- actual accepted step count;
- rejected internal steps if the provider exposes them;
- tolerances;
- actual final time.

`NumericalRunRecord.steps` represents accepted/output integration steps for adaptive execution. `requested_steps` records the caller's step-count hint where applicable.

Fixed-step convergence studies must not be reused blindly for adaptive methods. Adaptive validation should use tolerance refinement and work/error analysis instead.

## Provenance

Every tracked native/GPU run should identify at least:

- solver role;
- implementation ID;
- numerical method/pipeline ID;
- execution kind;
- backend;
- precision;
- requested step hint when applicable;
- accepted step count;
- start/end time;
- state size;
- semantic run tags.

Future extensions may add device/driver/compiler/kernel hashes without changing scientific-domain APIs.

## Error handling

Backend failures should be classifiable where practical:

- unsupported problem;
- allocation failure;
- device unavailable;
- numerical divergence/non-finite output;
- backend runtime failure;
- provider contract violation.

Do not convert every failure into a generic scientific-domain `ValueError` if provider context is important for fallback or diagnostics.

A product-level fallback policy may retry a compatible CPU/reference provider after a device failure, but scientific semantics must remain unchanged.

## Cancellation and long-running work

Native providers should eventually support cooperative cancellation for expensive simulations and sweeps. Cancellation belongs to the execution layer, not to physics/domain objects.

The first provider version may omit cancellation, but its ABI/API should avoid making later cancellation impossible.

## Renderer independence

Numerical providers must not import or depend on:

- `bpy`;
- Blender mesh/curve types;
- WebGPU rendering resources;
- Three.js/Godot/Unreal scene objects.

A numerical result becomes renderer-neutral field/trajectory/Scene semantics through the existing visualization pipeline.

## Reference validation protocol

Before a native/GPU provider can become a preferred/default implementation, validate it against trusted reference paths.

Minimum validation:

1. semantic result shape/type parity;
2. known analytical problems;
3. reference-solver comparison over several state sizes;
4. conservation/invariant metrics where applicable;
5. convergence or tolerance-refinement behavior;
6. float32/float64 error envelope;
7. deterministic repeated-run behavior where promised;
8. parameter-sweep batching parity;
9. execution provenance correctness;
10. fallback behavior for unsupported problems.

Performance numbers are useful only after numerical parity is demonstrated.

## Recommended first native provider

The lowest-risk first implementation is a native CPU first-order ODE solver, not a full GPU PDE stack.

Suggested progression:

```text
1. native CPU fixed-step RK4
2. native CPU adaptive RK45
3. batched native CPU ODE
4. GPU batched first-order ODE
5. GPU grid operators / method-of-lines kernels
6. fully device-resident PDE pipelines
```

This progression tests the solver-role abstraction before introducing complex device-memory lifetimes.

## Non-goals

This contract does not mandate:

- CUDA specifically;
- one universal buffer library;
- a particular FFI technology;
- synchronous execution forever;
- production-grade CFD/FDTD/FEA accuracy from reference domains;
- that every solver support every semantic problem.

It mandates that execution technology remains replaceable behind stable scientific/numerical contracts.
