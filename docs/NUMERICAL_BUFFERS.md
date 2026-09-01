# Spectra Science — Numerical Buffers and Data Layout

This document defines the intended execution-buffer boundary for high-performance numerical providers. It is a design contract, not yet a requirement that every current Python reference solver use a buffer object.

## Why this layer is needed

Scientific semantics currently use Python-native immutable objects such as tuples, dataclasses, fields, grids, and solution histories. That is appropriate for correctness and composition, but native/GPU execution needs contiguous, typed memory.

The intended split is:

```text
scientific semantic object
        ↓ pack/compile
execution buffer(s)
        ↓ numerical kernel
execution buffer(s)
        ↓ materialize/adapt
scientific result semantic
```

A future buffer abstraction must not replace scientific semantics. It is an execution representation.

## Core principles

1. Scientific domains describe meaning, not memory layout.
2. Numerical providers choose execution layouts behind stable contracts.
3. Buffer metadata must make dtype, shape, layout, and ownership explicit.
4. Copy boundaries must be observable and benchmarkable.
5. Renderer buffers and numerical buffers are separate by default.
6. Zero-copy is an optimization, never an implicit lifetime assumption.
7. Batch layout must preserve deterministic case correspondence.

## Minimal logical buffer descriptor

A future generic descriptor should be able to express at least:

- element dtype;
- logical shape;
- logical strides or contiguous-layout guarantee;
- memory location;
- mutability;
- ownership/lifetime;
- optional semantic component names;
- optional alignment requirements.

Conceptually:

```text
NumericalBufferDescriptor
    dtype       = float32 | float64 | complex64 | complex128 | int...
    shape       = (...)
    layout      = contiguous | strided
    location    = host | device | shared | external
    writable    = true/false
    ownership   = engine | provider | borrowed
```

This should remain independent from NumPy, CUDA, Metal, WebGPU, Blender, or a specific FFI library.

## Dtypes

Initial high-value numerical dtypes are:

```text
float32
float64
complex64
complex128
int32/int64 for indices where needed
```

Scientific APIs may continue exposing Python floats/complex values. The execution descriptor must report the actual compute/storage precision.

No provider may silently downcast while claiming a higher precision in execution metadata.

## Shape conventions

Prefer shapes that preserve the scientific grid/state structure rather than flattening everything at the public execution boundary.

Examples:

```text
first-order ODE state:       (state_size,)
scalar 2D grid:              (ny, nx)
scalar 3D grid:              (nz, ny, nx)
vector 2D grid:              (ny, nx, 2)
vector 3D grid:              (nz, ny, nx, 3)
N coupled scalar 3D fields:  (species, nz, ny, nx)
particle positions:          (count, 3)
```

Providers may internally transform these layouts when justified, but the transformation should not leak into scientific semantics.

## Canonical grid ordering

Existing `UniformGrid3D` flattening is logically:

```text
(z, y, x)
```

with x varying fastest.

Future buffer adapters should preserve this as the canonical host serialization order unless a versioned contract explicitly changes it.

This matters for:

- CPU/GPU parity;
- persisted arrays;
- native FFI;
- debugging;
- deterministic buffer hashes;
- slice/view reconstruction.

## AoS versus SoA

Neither Array-of-Structures nor Structure-of-Arrays should be globally mandated.

### Particle-like data

Semantic form:

```text
position[i] = (x, y, z)
velocity[i] = (vx, vy, vz)
```

Possible execution layouts:

AoS:

```text
[x,y,z, vx,vy,vz, ...]
```

SoA:

```text
x[] y[] z[] vx[] vy[] vz[]
```

A GPU/native provider may choose SoA for coalesced/vectorized operations while the semantic API remains unchanged.

### Vector grids

Canonical logical shape should remain `(nz, ny, nx, 3)`, even if a provider internally stores three component arrays.

The provider must own that layout conversion.

## Mutable execution, immutable semantics

Spectra semantic objects are generally easiest to reason about when immutable.

Execution buffers are often necessarily mutable and reused in-place.

That is intentional:

```text
immutable scientific intent
        ↓ compile
mutable provider-owned buffers
        ↓ many time steps
immutable/materialized scientific result
```

Do not make the scientific object mutable merely to achieve in-place GPU/CPU execution.

## Ownership states

A buffer should have one unambiguous ownership model.

### Engine-owned

The engine allocates and controls lifetime. A provider receives access for a bounded operation.

### Provider-owned

The numerical backend allocates native/device memory and owns cleanup.

### Borrowed

The buffer references external memory. Lifetime must be guaranteed by the caller for the full operation.

Borrowed buffers should be opt-in and explicit. They are useful for integrations but are dangerous as a default.

## Host/device location

Useful logical locations:

```text
host
host_pinned
device
shared
external
```

This is metadata, not an instruction that Core should import device APIs.

A provider may expose additional backend-specific detail in execution provenance.

## Copy policy

Initial native providers should prefer a simple and correct copy model:

```text
semantic tuples
    ↓ pack once
contiguous host buffer
    ↓ solve many steps
contiguous result buffer
    ↓ materialize once
semantic result
```

Only after profiling should the implementation move toward persistent buffers or zero-copy.

Copy count and copied bytes should become benchmark metrics.

## Persistent buffers

Persistent execution is useful for animations, long simulations, and parameter sweeps.

A future provider session may retain:

- state buffers;
- scratch buffers;
- grid geometry/constants;
- compiled kernels;
- factorization/preconditioner data;
- device allocations.

The session must still be separate from scientific semantics and renderer sessions.

Conceptually:

```text
NumericalSession
    prepare(problem)
    step/solve(...)
    readback(...)
    reset(...)
    close()
```

Do not introduce such a session until a concrete native provider needs it.

## Zero-copy rules

Zero-copy is allowed only when all of these are explicit:

1. source and consumer agree on dtype;
2. shape/layout are compatible;
3. lifetime is guaranteed;
4. mutation rights are clear;
5. synchronization is clear;
6. device/context ownership is compatible.

For example, a CUDA buffer is not automatically usable by a renderer just because both execute on the same GPU.

Cross-API sharing requires an explicit interop contract.

## Numerical ↔ renderer boundary

The default path remains:

```text
numerical result
    ↓ semantic field / trajectory / Scene
renderer backend
```

Do not couple solver device buffers directly to Blender or WebGPU renderer resources in the first implementation.

Later an optimized backend may add a specialized interop path, but the generic semantic path must remain available for correctness and portability.

## Batch layout

For independent cases, prefer an explicit leading batch dimension when problems have identical shape:

```text
(batch, state)
(batch, nz, ny, nx)
(batch, nz, ny, nx, components)
```

For heterogeneous problem sizes, use a batch descriptor with offsets/lengths rather than padding without limits.

Output ordering must correspond exactly to input ordering unless an explicit case-ID mapping accompanies the result.

## Complex values

Complex numerical fields may be represented as:

- native complex dtype;
- interleaved real/imag;
- separate real and imaginary arrays.

The execution provider chooses the physical layout.

The semantic contract remains complex-valued. Conversion must be lossless within the advertised precision.

## Sparse data

Dense regular grids should not force the design of sparse structures prematurely.

When sparse linear systems/meshes become a concrete provider requirement, introduce separate sparse descriptors such as CSR/CSC/COO with explicit index dtype and ownership.

Do not overload a dense buffer descriptor with hidden sparse semantics.

## Alignment and SIMD

Native CPU providers may require alignment for SIMD. Alignment belongs to the execution buffer descriptor/provider allocator, not the physics domain.

The provider should be able to request or allocate suitable memory without changing scientific problem classes.

## Synchronization

GPU execution introduces asynchronous completion. A future device buffer/session contract must distinguish:

- operation submitted;
- operation complete;
- host-readable result;
- buffer reusable;
- buffer safe to destroy.

The current synchronous solver role may initially synchronize before returning. An asynchronous API should be introduced separately rather than changing the meaning of an existing synchronous capability silently.

## Validation requirements

A numerical-buffer implementation should be validated for:

- shape/stride correctness;
- dtype correctness;
- grid flatten/unflatten parity;
- vector component order;
- complex encoding parity;
- copy ownership/lifetime;
- no use-after-free after provider cleanup;
- deterministic batch correspondence;
- host↔device round-trip error;
- no hidden precision downgrade.

## Benchmark metrics

Measure at least:

```text
pack time
host allocation time
device allocation time
host→device upload
kernel/solve time
device→host readback
semantic materialization time
peak allocated bytes
bytes copied per solve
```

A single `solve_ms` value is insufficient for architecture decisions.

## Recommended implementation order

```text
1. plain contiguous host descriptor
2. Python tuple ↔ host-buffer adapters
3. native CPU solver using host buffers
4. persistent native CPU workspace
5. device-buffer descriptor
6. GPU solver with explicit upload/readback
7. batched GPU execution
8. optional persistent device sessions
9. optional renderer interoperability
```

The buffer abstraction should emerge from these concrete needs rather than becoming a large speculative subsystem first.
