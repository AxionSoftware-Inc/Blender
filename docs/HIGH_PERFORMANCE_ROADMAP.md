# Spectra Science — High-Performance Execution Roadmap

This roadmap describes a low-risk path from the current Python reference numerical stack to native CPU and GPU execution without changing scientific-domain semantics.

The sequence is deliberately incremental. Each phase should validate the abstraction introduced by the previous phase before adding more execution complexity.

## Current starting point

The verified engine baseline already demonstrates:

- stable scientific/domain semantics;
- reusable ODE/PDE/math/physics capability composition;
- renderer-independent Scene/Timeline;
- native Blender incremental rendering behavior;
- runtime numerical solver roles;
- multiple reference solver implementations;
- solver selection metadata/policies;
- experiment/convergence/reproducibility foundations on the current post-baseline branch.

The next performance work should therefore improve execution rather than redesign scientific domains.

## Phase 1 — Native CPU first-order ODE

### Goal

Prove that the `ode.first_order` role can execute outside Python while every high-level consumer remains unchanged.

### Scope

Implement one native CPU fixed-step RK4 provider.

Possible implementation technologies:

- C++ shared library + Python binding;
- Rust + Python binding;
- C extension;
- another mature FFI path.

The choice is secondary to the role/result contract.

### Required behavior

- same `FirstOrderSystem` semantic input;
- same `ODESolution` output;
- execution metadata reports `cpu` and native backend;
- provider is optional/loadable;
- problem compatibility is explicit;
- reference RK4 remains available;
- solver comparison/convergence parity passes.

### Success gate

Native CPU should show a meaningful benefit for medium/large state vectors while producing fourth-order convergence and stable repeated-run memory.

Do not move to GPU merely because the binding loads successfully.

## Phase 2 — Native contiguous numerical buffers

### Goal

Remove repeated Python tuple element overhead from native execution.

### Scope

Introduce the minimal concrete buffer descriptor/adapters required by the Phase-1 provider.

Start with:

```text
float64 1D contiguous host state
```

then extend only as needed.

### Success gate

- pack/unpack behavior is explicit;
- copy counts are benchmarked;
- state ordering is deterministic;
- no semantic-domain API changes;
- no dependency on NumPy as a scientific semantic requirement.

## Phase 3 — Native adaptive ODE

### Goal

Validate adaptive execution/provenance outside Python.

### Scope

Implement native Dormand-Prince/RK45 or another compatible adaptive method.

### Required provenance

- requested initial step hint;
- accepted steps;
- tolerances;
- implementation/backend/precision;
- actual final time.

### Validation

Use tolerance-refinement/work-error studies rather than fixed-step convergence.

## Phase 4 — Batched native CPU execution

### Goal

Make parameter studies and many independent trajectories efficient without GPU complexity.

### Scope

Support a leading batch dimension for identical-shape problems.

Useful workloads:

- parameter sweeps;
- Monte-Carlo-like future sampling;
- particle-independent trajectories;
- calibration candidate grids;
- solver comparison runs.

### Success gate

- deterministic input/output case ordering;
- batched experiment API integration;
- throughput benefit over repeated scalar calls;
- bounded memory behavior.

## Phase 5 — GPU batched ODE provider

### Goal

Prove GPU provider selection and device-buffer contracts on a mathematically simple workload.

### Why ODE first

A batched ODE avoids immediately combining:

- complex grid stencils;
- boundary conditions;
- sparse solves;
- pressure projection;
- renderer interop.

It isolates execution architecture.

### Initial target

Large batches of identical-shape first-order systems.

### Success gate

- GPU policy selects only compatible problems;
- CPU/reference fallback works;
- float32/float64 precision is truthful;
- upload/kernel/readback are measured separately;
- batch throughput demonstrates a clear target workload advantage;
- experiment traces record the GPU implementation per case/batch.

## Phase 6 — Persistent GPU workspace

### Goal

Avoid upload/allocation/readback on every integration segment.

### Scope

Introduce a provider execution session only after profiling proves it is useful.

Potential lifecycle:

```text
prepare(problem shape/constants)
allocate persistent buffers
upload initial state
run many steps / parameter variants
selective readback
close
```

### Non-goal

Do not make the generic scientific `DomainRegistry` a device-context manager.

## Phase 7 — GPU regular-grid operators

### Goal

Accelerate the universal PDE building blocks rather than writing one GPU solver per subject.

Prioritize reusable kernels:

- 2D/3D Laplacian;
- gradient;
- divergence;
- curl;
- advection;
- grid integrals/reductions.

This creates broad reuse across:

- diffusion/heat;
- waves;
- Schrödinger;
- fluid diagnostics;
- electrostatics/gravity;
- Maxwell;
- reaction-diffusion.

### Success gate

Grid operator parity must be validated independently before full PDE pipelines rely on them.

## Phase 8 — Device-resident method-of-lines PDE

### Goal

Avoid host materialization between spatial operators and ODE integration stages.

Conceptual path:

```text
semantic PDE problem
    ↓ compile once
persistent device state
    ↓
GPU spatial RHS
    ↓
GPU time integrator
    ↓ repeated entirely on device
selective snapshots/readback
```

### Critical rule

The high-level PDE/physics semantic result contract stays stable even if the execution provider keeps internal state on device.

## Phase 9 — Elliptic/native linear solvers

Poisson and future finite-element/implicit systems need a separate linear-solver role architecture rather than being forced into the ODE role.

Potential future roles:

```text
linear.solve_dense
linear.solve_sparse
elliptic.solve_poisson
nonlinear.solve
```

Introduce these only when concrete implementations and comparison problems exist.

## Phase 10 — Renderer interoperability

Only after solver/device buffers are mature should Spectra consider direct numerical-buffer to renderer-buffer interoperability.

Potential benefit:

```text
GPU simulation state
    ↓ no host readback
GPU renderer attributes/vertices
```

But the generic path must remain:

```text
numerical result
    ↓ semantic field/Scene
renderer backend
```

Direct interop is an optional optimization, not the architecture's source of truth.

## Performance target philosophy

Do not optimize every workload for the same backend.

Expected shape:

```text
small problem        -> Python/reference or CPU may win
medium dense state   -> native CPU likely wins
large batched state  -> GPU may win
interactive renderer -> incremental Scene/backend path matters
large PDE grid       -> device residency matters more than launch latency
```

Solver policies should encode this reality through compatibility/requirements rather than one global `use_gpu=True` switch.

## Required benchmark dimensions

Every performance phase should report:

- problem/state size;
- batch size;
- precision;
- packing time;
- upload/readback time when applicable;
- solve/kernel time;
- end-to-end time;
- memory peak;
- numerical error/invariant residual;
- implementation ID;
- device/backend metadata.

See `docs/NUMERICAL_BACKEND_VALIDATION.md`.

## ABI and packaging discipline

Native-provider work should keep packaging isolated from scientific modules.

Recommended separation:

```text
spectra semantic Python package
spectra native provider package/module
optional device runtime dependencies
```

A user who only needs reference Python execution or Blender rendering should not be forced to install CUDA/native build tooling.

## Cross-platform direction

Prefer an architecture that can eventually support:

```text
Windows
Linux
macOS
```

Native CPU should be portable first. GPU provider families may differ by platform (for example CUDA versus Metal/WebGPU), but they should implement the same stable numerical roles.

## What should not happen

Do not:

- rewrite physics domains in C++/CUDA one by one;
- expose raw device pointers in scientific APIs;
- make Blender the owner of simulation buffers;
- make GPU availability mandatory for ordinary imports;
- make one giant native library that knows every scientific subject;
- replace reference solvers after only a speed benchmark;
- claim GPU acceleration without counting upload/readback costs;
- hide precision changes;
- hardcode device checks throughout product/domain code.

## Milestone sequence

A practical sequence is:

```text
M1  native CPU RK4 parity
M2  host buffer abstraction
M3  native adaptive RK45
M4  batched native CPU
M5  GPU batched ODE
M6  persistent GPU workspace
M7  GPU universal grid operators
M8  device-resident PDE time integration
M9  native/GPU elliptic and linear-solver roles
M10 optional numerical/render interop
```

Each milestone should leave the scientific-domain code essentially unchanged. If a performance milestone requires broad physics/chemistry rewrites, the execution abstraction is leaking and should be reconsidered.
