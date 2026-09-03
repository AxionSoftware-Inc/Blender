# Spectra Science — Native Numerical Provider API Draft

Status: **design draft, not implemented runtime**.

This document converts the native/GPU execution architecture into a concrete provider shape using the **existing** numerical runtime.

## Source-of-truth result

Current runtime already provides the important abstractions:

```text
NumericalMethodDescriptor
NumericalPipelineDescriptor
NumericalExecutionDescriptor
NumericalSolverRequirements
NumericalSolverPolicy
NumericalSolverImplementation
NumericalSolverRegistry
DomainRegistry.register_numerical_solver(...)
problem compatibility predicate
policy/select/resolve
transactional DomainRegistry rollback
tracked NumericalRunRecord
```

Therefore a native provider does **not** need:

```text
another solver registry
another solver-selection system
another provenance system
another provider transaction model
```

It should plug into the existing role runtime.

## Goal

```text
scientific domain
   -> ode.solve_first_order
   -> NumericalSolverRegistry
   -> rk4.reference / heun.reference / rk45.reference
   -> rk4.native_cpu / future gpu implementations
```

Execution technology changes; scientific APIs do not.

## First provider target

Recommended first implementation after the pending runtime validation:

```text
role: ode.first_order
implementation_id: rk4.native_cpu
execution kind: cpu
precision: float64
adaptive: false
order: 4
reference implementation: false
```

Do not start with GPU/CFD/multiphysics.

## Exact current registration path

Use current `DomainRegistry.register_numerical_solver(...)` directly:

```python
registry.register_numerical_solver(
    role="ode.first_order",
    implementation_id="rk4.native_cpu",
    solver=solve_native_rk4,
    method=NumericalMethodDescriptor(
        method_id="rk4.fixed.native_cpu",
        family="runge_kutta",
        implementation="native_cpu",
        order=4,
        adaptive=False,
        reference_implementation=False,
    ),
    execution=NumericalExecutionDescriptor(
        kind="cpu",
        backend="native_cpu",
        precision="float64",
        supports_in_place=False,
        batched=False,
    ),
    supports_problem=supports_native_problem,
    priority=..., 
    tags=("native", "cpu"),
)
```

Current `DomainRegistry` automatically records the active provider domain into `NumericalSolverImplementation.provider_domain`.

Therefore do not duplicate provider-domain metadata in another binding structure.

## Provider domain

Expose the implementation through an ordinary domain:

```python
class NativeCpuOdeDomain:
    name = "numerics.native_cpu.ode"
    version = "1"
    dependencies = (
        DomainDependency("ode.first_order_system"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_numerical_solver(...)
        registry.provide(
            "ode.first_order.rk4_native_cpu",
            registry.numerical_solvers.implementation(
                "ode.first_order",
                "rk4.native_cpu",
            ),
            version=1,
        )
```

Exact marker capability may be adjusted, but capability-driven provider loading should reuse normal DomainCatalog behavior.

## Existing solver selection already supports native providers

Current runtime can already filter/select by:

```text
execution kind: python/cpu/gpu/external
precision
minimum order
adaptive/fixed
reference allowed/disallowed
tags
priority
problem predicate
ordered policy rules
fallback to default
```

A native provider only needs correct metadata and compatibility rules.

## Problem compatibility

Current `NumericalSolverImplementation.accepts_problem(...)` already invokes an optional predicate.

Use it to express native limitations explicitly.

Example:

```python
def supports_native_problem(problem: FirstOrderODEProblem) -> bool:
    return (
        problem.state_size <= MAX_STATE_SIZE
        and problem.supports_plain_real_state
    )
```

Do not make a high-priority provider appear universally compatible if it is not.

## Precision

Current `NumericalExecutionDescriptor.precision` and `NumericalSolverRequirements.precisions` already support explicit selection.

Therefore:

```text
float64 requested
+ provider only float32
```

must result in provider rejection/fallback, not silent downcast.

## Execution metadata

Current `NumericalExecutionDescriptor` already contains:

```text
kind
backend
precision
device
supports_in_place
batched
```

Use these fields before introducing another provider execution descriptor.

Example later GPU implementation:

```python
NumericalExecutionDescriptor(
    kind="gpu",
    backend="cuda",
    precision="float32",
    device="cuda:0",
    supports_in_place=True,
    batched=True,
)
```

Device identity may need more durable provenance conventions later; do not serialize process pointers/handles.

## Provenance

Current `NumericalRunRecord` already supports:

```text
method/pipeline
start/end time
accepted/current steps
requested_steps
state_size
solver_role
implementation_id
execution_kind
backend
precision
```

Native tracked solve should populate these same fields.

Provider package/library version may be added as a run tag or environment snapshot metadata initially rather than redesigning `NumericalRunRecord` immediately.

## ABI boundary

The remaining real design problem is not solver selection. It is the Python↔native execution boundary.

First provider bridge:

```text
FirstOrderODEProblem
    ↓ validate/pack
contiguous y0 + time interval + steps
    ↓ native RK4 call
contiguous times/states
    ↓ materialize
ODESolution
```

Native library should know nothing about:

```text
DomainRegistry
Scene
Blender
PresentationIntent
ProjectDocument
```

## Callback warning

A generic first-order ODE problem currently carries Python-callable RHS semantics.

If native RK4 calls back into Python for every RHS evaluation, native loop speedup may be small or negative.

Therefore P1 should measure two things separately:

```text
native loop overhead with Python callback
pure native compiled/simple RHS proof
```

Do not claim native acceleration based only on kernel timing that ignores callback/marshaling cost.

## Draft low-level C ABI

Illustrative only:

```c
int spectra_ode_rk4_f64(
    spectra_rhs_f64 rhs,
    void* user_data,
    double t0,
    double t1,
    const double* y0,
    size_t state_size,
    size_t steps,
    double* out_times,
    double* out_states
);
```

Before freezing ABI, prove:

- ownership;
- callback behavior;
- error mapping;
- GIL behavior;
- state layout;
- batching needs.

## Memory ownership

Rules:

- semantic Python object owned by engine/caller;
- temporary packed host buffer owned by bridge;
- native call cannot retain borrowed pointer after return unless lifecycle says so;
- output memory has one explicit owner;
- C ABI exceptions never cross language boundary;
- GPU pointers never become persistent project artifact fields.

## Buffer abstraction

Do not introduce a general `NumericalBuffer` runtime before P1 proves what is actually required.

After P1/P2, promote evidence-backed concepts from `NUMERICAL_BUFFERS.md`, likely:

```text
dtype
shape
memory space
ownership
host/device identity
```

Python reference solvers do not need to be rewritten through that buffer API immediately.

## Native errors

Map native failures into distinguishable categories:

```text
provider_unavailable
unsupported_problem
invalid_buffer
precision_unavailable
native_execution_failed
out_of_memory
non_finite_result
cancelled
```

Do not misreport an ABI/device/provider failure as invalid physics.

## GIL/threading

If the native loop does not call Python RHS callbacks, a CPython extension may release the GIL during computation.

If it does call Python, callback synchronization cost must be measured.

Benchmark reports should include thread count and backend/device metadata where relevant.

## Determinism/parity

Required claim is numerical parity within tolerance, not cross-platform bitwise identity unless explicitly promised.

Separate:

```text
method semantics
floating-point tolerance
bitwise reproducibility
```

## Validation matrix for `rk4.native_cpu`

Before preferred/default eligibility:

1. scalar exponential ODE parity;
2. harmonic oscillator parity;
3. multi-state linear system parity;
4. observed RK4 convergence order ~4;
5. invalid state/RHS handling;
6. non-finite output handling;
7. repeated-run tolerance consistency;
8. `NumericalExecutionDescriptor` correct;
9. tracked `NumericalRunRecord` correct;
10. explicit requirement selects native CPU;
11. fallback selects reference when native problem predicate rejects;
12. high-level mechanics uses native solver without mechanics source changes;
13. one PDE method-of-lines case routes through native role without PDE source changes.

## Performance reporting

Report separately:

```text
semantic validation/pack
Python->native transition
native compute
native->Python materialization
total solve API
```

For batch providers later:

```text
cases/sec
state elements/sec
batch latency
transfer bytes/time
```

## GPU evolution

After native CPU proves the role boundary:

```text
rk4.native_cpu
   ↓
batched native CPU or adaptive native
   ↓
evidence-backed buffer contract
   ↓
GPU batched ODE
   ↓
GPU grid operators
   ↓
device-resident PDE pipelines
```

GPU implementations register through the exact same `NumericalSolverRegistry` model.

## Strong architectural regression

This is the most important test:

```text
same semantic mechanics/PDE problem
    -> solve with reference provider
    -> register/select native provider
    -> solve again
    -> no domain source/API change
    -> compare results within tolerance
```

If native execution requires editing heat/Maxwell/chemistry/mechanics formulas, the role boundary failed.

## Success criterion

The native provider can be installed, selected, benchmarked, and removed while the scientific domain graph remains unchanged. Removing it simply lets existing solver policy/defaults fall back to reference implementations.