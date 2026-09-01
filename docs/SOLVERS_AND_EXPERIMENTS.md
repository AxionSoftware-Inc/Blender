# Spectra Science — Solvers, Experiments, and Reproducibility

This document describes the numerical execution layer that sits underneath scientific domains without making Core depend on any particular solver technology.

## Separation of responsibilities

Spectra uses two related but different mechanisms:

```text
DomainCatalog / capabilities
    -> discover and load the scientific/numerical provider domain

NumericalSolverRegistry
    -> choose one loaded implementation for a stable solver role at runtime
```

A capability answers **what functionality/domain must be available**. A solver role answers **which loaded implementation should execute that numerical contract**.

For example, the first-order ODE role is:

```text
ode.first_order
```

The default implementation is currently:

```text
rk4.reference
```

An optional provider domain adds:

```text
heun.reference
```

without replacing the existing `ode.solve_rk4` compatibility capability.

## Role-dispatched composition

High-level scientific domains should not depend on a concrete implementation name such as RK4. They depend on the stable dispatch capability:

```text
ode.first_order_system
ode.solve_first_order >= 2
```

`ode.solve_first_order` resolves the current default implementation of the `ode.first_order` role when it is called.

This means a stack such as:

```text
native/GPU first-order solver
        ↓
ode.first_order role
        ↓
method-of-lines PDE
        ↓
wave / heat / chemistry / fluid / quantum / solid dynamics
```

can change execution implementation without changing the scientific domain code.

The legacy/reference capability `ode.solve_rk4` remains available for compatibility, direct reference testing, and controlled comparisons.

## Loading optional implementations

A solver-provider domain should expose at least one ordinary discoverable capability in addition to registering its runtime implementation.

The built-in Heun provider demonstrates this pattern:

```text
capability: ode.first_order.heun_reference
provider:   differential_equations.reference_solvers
runtime:    ode.first_order / heun.reference
```

Capability-driven loading can then be used:

```python
catalog.load_capabilities(
    registry,
    ("ode.first_order.heun_reference",),
)
```

The catalog resolves and loads the provider's dependency closure. During registration, the provider calls `registry.register_numerical_solver(...)`.

A future native/GPU provider should follow the same structure, for example:

```text
capability: ode.first_order.native_gpu
provider domain loads
    ↓
registry.register_numerical_solver(
    role="ode.first_order",
    implementation_id="rk4.cuda",
    ...
)
```

No central solver switch statement is required.

## Execution metadata

Each numerical implementation can describe execution independently from scientific semantics:

- execution kind: `python`, `cpu`, `gpu`, or `external`
- backend identifier
- precision
- optional device identifier
- in-place support
- batched execution support
- priority
- tags

Selection requirements can constrain:

- execution kind
- precision
- minimum numerical order
- adaptive/fixed behavior
- whether reference implementations are allowed
- required implementation tags

This supports policies such as:

```text
prefer GPU
require float32
require batched support
minimum order >= 4
exclude reference implementations
```

without teaching physics/PDE domains about CUDA, Metal, WebGPU, NumPy, or any other execution backend.

## Problem compatibility

Execution metadata alone is insufficient. A native implementation may support only certain semantic problems or state sizes.

A solver implementation may therefore provide a `supports_problem` predicate. Selection can use:

```python
registry.select_numerical_solver_for_problem(
    role,
    problem,
    requirements,
)
```

Only implementations satisfying both the execution requirements and the semantic problem predicate are candidates.

This is intentionally a runtime compatibility check. Domain/capability discovery remains the mechanism for loading the provider itself.

## Numerical provenance

Reference solvers expose method descriptors and tracked execution records.

A tracked run records, where applicable:

- method/pipeline identity
- start/end time
- step count
- fixed step size
- state size
- semantic tags

For a 3D method-of-lines PDE, provenance is composed dynamically:

```text
method-of-lines scalar 3D
        +
currently selected ode.first_order implementation
        ↓
current numerical pipeline descriptor
```

This is important because changing the runtime ODE default must also change the reported numerical provenance. A static declaration that always claimed RK4 would be incorrect.

## Parameter sweeps

The `experiments` domain provides deterministic Cartesian parameter sweeps:

```text
ParameterAxis × ParameterAxis × ...
        ↓
deterministic ParameterCase IDs
        ↓
case evaluator
        ↓
unit-aware metrics
        ↓
ExperimentResult
```

Failure policy can either raise immediately or record an error for the failed case.

Parameter values are intentionally generic semantic values. A scientific domain can therefore sweep plain numbers, quantities, model choices, boundary modes, or other immutable semantic objects.

## Batched experiments

`experiments.batching` provides a batch evaluator contract for vectorized/native/GPU workflows.

A sweep is still deterministic, but cases are supplied to the evaluator in stable batches:

```text
5 cases, batch_size=2
    -> [0,1]
    -> [2,3]
    -> [4]
```

The evaluator must return one output per input case. Batch failures can either raise or be recorded for every case in that failed batch.

This layer does not assume CUDA/WebGPU/NumPy. It only establishes the batching contract that such implementations can consume later.

## Solver comparison

`experiments.compare_solvers` executes the same problem and solver keyword arguments across multiple implementations of one role.

Metrics are evaluated on every result, enabling comparisons such as:

- absolute/relative solution error
- conservation residual
- final energy error
- divergence residual
- domain-specific validation metrics

The built-in RK4 and optional Heun reference implementations provide a real comparison path rather than a test-only mock architecture.

## Convergence studies

`experiments.convergence` runs a fixed-step solver implementation over increasing step counts and computes observed convergence order:

```text
p ≈ log(error_coarse / error_fine)
     --------------------------------
     log(step_coarse / step_fine)
```

The result also carries the method's declared order when available, allowing an observed-vs-declared consistency check.

Reference tests use exponential growth `y' = y` to verify approximately fourth-order behavior for RK4 and second-order behavior for Heun.

Convergence tests are an important parity tool for future native/GPU implementations: a faster solver should preserve the expected numerical contract rather than merely produce visually plausible output.

## Reproducibility snapshots

`spectra.reproducibility.capture_environment(registry)` records the currently loaded scientific environment:

- domain names and versions
- capability names, versions, and provider domains
- numerical solver roles/implementation IDs
- method IDs
- execution kind/backend/precision
- default solver selection
- priority/tags

The canonical snapshot produces a deterministic SHA-256 fingerprint.

Tracked experiments can store this environment snapshot alongside the result. If the scientific environment changes, the fingerprint changes.

This fingerprint is an engine-environment fingerprint, not a replacement for source-control revision, input-data hashes, or platform/compiler metadata. Those can be layered on later when execution packaging requires them.

## Extension rule for native/GPU solvers

A new implementation should normally:

1. live in a provider domain/plugin rather than Core;
2. depend on the stable solver-role capability it implements;
3. expose a normal capability so DomainCatalog can discover/load it;
4. register a unique implementation ID in `NumericalSolverRegistry`;
5. provide method and execution metadata;
6. optionally provide a semantic problem compatibility predicate;
7. preserve the common role call contract;
8. be validated with solver comparison and convergence studies;
9. avoid leaking backend-specific concepts into scientific domains.

The intended result is:

```text
science semantics stay stable
        ↓
numerical role stays stable
        ↓
reference Python / native CPU / GPU / external solver can change
```

That is the execution boundary Spectra needs before high-performance numerical backends are introduced.
