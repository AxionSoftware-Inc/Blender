# Spectra Science — Native Numerical Provider API Draft

Status: **design draft, not implemented runtime**.

This document converts the native/GPU execution architecture into a concrete Python-facing provider API shape. It is intentionally designed around the existing numerical-role model so scientific domains remain unchanged.

## Goal

A native CPU/GPU provider should register another implementation of an existing numerical role:

```text
scientific domain
   -> ode.solve_first_order
   -> NumericalSolverRegistry
   -> rk4.reference / heun.reference / rk45.reference
   -> future rk4.native_cpu / rk45.native_cpu / cuda.*
```

The provider must change execution technology, not scientific meaning.

## First provider target

The recommended first implementation after the numerical-runtime validation is:

```text
role: ode.first_order
implementation: rk4.native_cpu
```

Do not start with GPU, CFD, or a multiphysics solver.

Why:

- simple reference parity target;
- formal order is known;
- many higher-level domains already consume the role;
- proves ABI/buffer/provider/provenance path;
- does not require GPU availability.

## Provider descriptor

Suggested immutable metadata:

```python
@dataclass(frozen=True)
class NativeProviderDescriptor:
    provider_id: str
    version: str
    execution_kind: str       # cpu | gpu | external
    device_api: str | None    # native | cuda | metal | vulkan | webgpu | remote
    precision: tuple[str, ...]
    roles: tuple[str, ...]
    tags: tuple[str, ...] = ()
    reference_compatible: bool = True
```

This describes the provider package/library, not one solver method.

## Solver implementation registration

Use the existing numerical registry model.

Conceptual adapter:

```python
@dataclass(frozen=True)
class NativeSolverBinding:
    role: str
    implementation_id: str
    method: NumericalMethodDescriptor
    execution: NumericalExecutionDescriptor
    solver: Callable[..., object]
    supports_problem: Callable[[object], bool] | None = None
    priority: int = 0
    tags: tuple[str, ...] = ()
```

Registration remains conceptually:

```python
registry.register_numerical_solver(
    role=binding.role,
    implementation_id=binding.implementation_id,
    solver=binding.solver,
    method=binding.method,
    execution=binding.execution,
    supports_problem=binding.supports_problem,
    priority=binding.priority,
    tags=binding.tags,
)
```

Do not create a separate `NativeSolverRegistry`.

## Provider domain

A native provider should normally be exposed through an ordinary domain/plugin module:

```python
class NativeCpuOdeDomain:
    name = "numerics.native_cpu.ode"
    version = "1"
    dependencies = (...)

    def register(self, registry: DomainRegistry) -> None:
        ... register numerical implementation ...
        registry.provide("ode.first_order.rk4_native_cpu", marker_or_descriptor, version=1)
```

This allows capability-driven loading and plugin packaging to reuse the same domain/catalog architecture.

## ABI boundary

Python semantic objects should not be the long-term native ABI.

For the first provider, keep the bridge narrow:

```text
FirstOrderODEProblem
    ↓ validate/pack
contiguous state buffer + time interval + parameters
    ↓ native call
contiguous times/states
    ↓ materialize
ODESolution
```

The native library should not know about Blender, Scene, DomainRegistry, project files, or presentation.

## Draft low-level call shape

For a C ABI, a simple first shape could be conceptually:

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

This is illustrative, not a frozen ABI.

The first implementation should prove:

- ownership rules;
- error propagation;
- callback cost;
- parity;
- packaging.

If Python callback overhead dominates, later native problem compilation/batched RHS contracts can evolve without changing the scientific role.

## Memory ownership

Rules:

- Python owns semantic input objects;
- bridge owns temporary packed host buffers unless an explicit zero-copy contract applies;
- native solver must not retain pointers after return unless lifecycle explicitly supports it;
- returned native memory must have one clear owner/release function;
- exceptions must not cross C ABI boundaries;
- GPU device pointers must never be serialized into project/result artifacts.

## Buffer descriptor direction

A later generic buffer runtime may use:

```python
@dataclass(frozen=True)
class NumericalBufferView:
    dtype: str
    shape: tuple[int, ...]
    strides: tuple[int, ...] | None
    memory_space: str      # host | pinned_host | device
    device: str | None
    readonly: bool
```

Do not force this abstraction into all Python reference solvers before the first native provider demonstrates the actual need.

## Error contract

Native provider errors should map to structured classes/categories:

```text
provider_unavailable
unsupported_problem
invalid_buffer
precision_unavailable
native_execution_failed
device_lost
out_of_memory
non_finite_result
cancelled
```

A provider crash must not be misreported as a scientific validation failure.

For in-process native libraries, hard crashes cannot be fully isolated; that risk belongs to plugin/provider trust policy.

## Problem compatibility

Native implementations may support only subsets.

Example:

```python
def supports_problem(problem: FirstOrderODEProblem) -> bool:
    return (
        problem.state_size <= MAX_STATE
        and problem.is_real
        and not problem.requires_python_side_effects
    )
```

Solver selection already needs to respect this predicate.

Do not select a GPU/native solver solely because its priority is high.

## Precision

A provider must declare supported precision explicitly.

Examples:

```text
float64
float32
complex128
complex64
```

Never silently execute a float64 request as float32.

If precision is unavailable, selection should reject the implementation and continue fallback policy where allowed.

## Provenance

Tracked execution must record at least:

```text
solver role
implementation ID
method ID
provider ID/version
execution kind
device API/device identity where appropriate
precision
requested steps/tolerance
accepted steps where meaningful
```

Project/experiment artifacts should store durable identifiers and metadata, not process pointers.

## Cancellation

First native CPU provider may omit cooperative cancellation if the call is short, but API design should not preclude it.

Long-running native/GPU/remote providers should eventually accept a cancellation token or callback.

Cancellation must return a distinct status, not a corrupted partial success.

## Threading

Do not assume the Python GIL must remain held during pure native computation.

A CPython extension/provider may release the GIL while executing native loops if callbacks into Python are not occurring.

Record thread count/environment in benchmark reports where it affects results.

## Determinism

Reference parity should distinguish:

- deterministic method semantics;
- floating-point reproducibility;
- cross-device bitwise identity.

Native/GPU providers need numerical tolerance parity, not necessarily bit-for-bit equality across architectures unless explicitly claimed.

## First provider package layout

Possible built-in development layout:

```text
native/
  ode_cpu/
    CMakeLists.txt
    include/
    src/

spectra/providers/
  native_cpu/
    __init__.py
    ode.py
    domain.py
```

Exact layout is not yet frozen.

If externalized, use the plugin model instead of hardwiring vendor/provider code into Core.

## Validation matrix for rk4.native_cpu

Must pass before becoming preferred:

1. scalar exponential ODE parity;
2. harmonic oscillator parity;
3. multi-state linear system parity;
4. RK4 observed convergence order ~4;
5. non-finite RHS handling;
6. invalid state length handling;
7. deterministic repeated run within tolerance;
8. tracked provenance correctness;
9. solver policy explicit selection;
10. high-level mechanics or PDE uses native provider without domain code changes.

## Performance reporting

Report separately:

```text
pack/validation time
native solve time
materialization time
total API time
```

Otherwise a fast kernel with expensive Python↔native marshaling can look misleading.

For batch workloads report:

```text
cases/sec
state elements/sec
latency per batch
```

## GPU evolution

Once native CPU provider proves the contract:

```text
native CPU ODE
  -> typed contiguous buffers
  -> batched ODE API
  -> GPU batch provider
  -> GPU grid operators
  -> device-resident PDE pipeline
```

GPU provider should reuse the same role/selection/provenance interfaces.

## Scientific-domain invariance test

The strongest architectural regression is:

```text
load high-level PDE/mechanics domain
solve using reference default
register/select native provider
solve same semantic problem
assert domain source/API unchanged
compare result within tolerance
```

If enabling native execution requires editing Maxwell/heat/chemistry/mechanics implementations, the provider boundary has failed.

## Success criterion

The first native CPU provider should be removable from the environment with no change to scientific domain APIs; the engine should simply fall back to reference implementations through the same solver role.