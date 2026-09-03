# Spectra Science — Native CPU ODE Provider Implementation Blueprint

Status: **implementation blueprint; no native runtime code has been added yet**.

This document is the file-by-file plan for the first native numerical provider after the pending Python runtime validation is green.

## Architectural target

Current executable source already defines:

```text
FirstOrderSystem
ODESolution
ODE_FIRST_ORDER_SOLVER_ROLE = "ode.first_order"
rk4.reference
DomainRegistry.register_numerical_solver(...)
problem-aware selection/policy
tracked provenance
```

The first native provider therefore adds only another implementation:

```text
ode.first_order / rk4.native_cpu
```

Scientific domains must remain unchanged.

## Scope of first native checkpoint

The first checkpoint proves:

1. optional native provider packaging/load;
2. semantic `FirstOrderSystem` adapter;
3. native fixed-step RK4 execution;
4. `ODESolution` materialization;
5. `NumericalExecutionDescriptor(kind="cpu", ...)`;
6. role registration;
7. explicit/default/policy selection;
8. tracked provenance;
9. reference parity/convergence;
10. high-level domain dispatch without source changes.

It does **not** need to prove major performance improvement yet because arbitrary Python RHS callbacks can dominate runtime.

## Recommended repository shape

Keep native provider implementation separable from the central semantic package.

Proposed monorepo development layout:

```text
providers/
  native_cpu/
    pyproject.toml
    README.md
    src/
      spectra_native_cpu/
        __init__.py
        domain.py
        ode.py
        diagnostics.py
      native/
        ode_rk4.c
        ode_rk4.h
        module.c
    tests/
      test_native_cpu_provider.py
      test_native_cpu_parity.py
      test_native_cpu_dispatch.py
```

Alternative built-in package layout is acceptable later, but first proof should preserve the ability to uninstall/remove the provider without touching `spectra/` scientific code.

## Packaging choice

Current root project uses setuptools and has no runtime dependencies.

For the first provider, prefer one of these in order:

### Option A — separate CPython C extension package

Advantages:

- no pybind11 runtime/build dependency required beyond normal compiler/Python headers;
- direct Python exception mapping;
- wheel packaging can be isolated;
- provider remains optional.

### Option B — C ABI shared library + ctypes bridge

Advantages:

- explicit ABI;
- easier reuse from other languages.

Disadvantages:

- callback/ownership/error glue can be more awkward;
- shipping/loading platform library paths needs care.

### Do not start with

- CUDA;
- Rust toolchain;
- CMake-heavy multi-library architecture;
- native PDE implementation;
- native ownership of DomainRegistry.

The first checkpoint is a contract proof.

## Python provider package

### `spectra_native_cpu/domain.py`

Conceptual domain:

```python
class NativeCpuOdeDomain:
    name = "numerics.native_cpu.ode"
    version = "1"
    dependencies = (
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solution"),
        DomainDependency("ode.solver_role.first_order"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_numerical_solver(
            "ode.first_order",
            "rk4.native_cpu",
            solve_rk4_native_cpu,
            RK4_NATIVE_CPU_METHOD,
            make_default=False,
            priority=10,
            tags=("native", "cpu", "fixed-step"),
            execution=RK4_NATIVE_CPU_EXECUTION,
            supports_problem=supports_native_cpu_problem,
        )
        registry.provide(
            "ode.first_order.rk4_native_cpu",
            RK4_NATIVE_CPU_METHOD,
            version=1,
        )
```

Do not overwrite `ode.solve_rk4` or `rk4.reference`.

## Method metadata

Conceptual:

```python
RK4_NATIVE_CPU_METHOD = NumericalMethodDescriptor(
    method_id="rk4.fixed",
    family="explicit-runge-kutta",
    implementation="spectra.native_cpu.rk4",
    order=4,
    adaptive=False,
    reference_implementation=False,
    notes=("native CPU fixed-step RK4 provider",),
)
```

Same mathematical method ID/family/order; different implementation identity.

Execution:

```python
RK4_NATIVE_CPU_EXECUTION = NumericalExecutionDescriptor(
    kind="cpu",
    backend="spectra.native_cpu",
    precision="float64",
    supports_in_place=False,
    batched=False,
)
```

Provider/version information can later be added to durable provenance without changing solver role semantics.

## Problem compatibility

First provider accepts only the exact current real-valued first-order system contract.

Conceptual predicate:

```python
def supports_native_cpu_problem(problem: object) -> bool:
    return (
        isinstance(problem, FirstOrderSystem)
        and len(problem.initial_state) > 0
        and all(math.isfinite(v) for v in problem.initial_state)
        and callable(problem.derivative)
    )
```

If callback strategy imposes state-size/platform limits, make them explicit here.

Never select native merely because it exists.

## Native call boundary

First C extension API may expose one Python-visible function:

```python
_native.solve_rk4(
    derivative,
    initial_time: float,
    initial_state: tuple[float, ...],
    end_time: float,
    steps: int,
) -> tuple[tuple[float, ...], tuple[tuple[float, ...], ...]]
```

The public provider adapter converts this to `ODESolution`.

The C extension is execution plumbing; it does not return/construct DomainRegistry or Scene objects.

## C-side state layout

Use contiguous row-major double buffers:

```text
y[state_size]
k1[state_size]
k2[state_size]
k3[state_size]
k4[state_size]
tmp[state_size]
out_states[(steps + 1) * state_size]
out_times[steps + 1]
```

Validate multiplication/size overflow before allocation.

No pointer is retained after the solve call returns.

## Python derivative callback

For checkpoint 1, C may call the supplied Python derivative at each RK stage.

Required validation per callback:

- returned sequence length == state size;
- all values convertible to finite double;
- exception propagates as provider execution failure/normal Python exception without corrupting memory.

This path proves integration but is **not expected to deliver maximal speed**.

Performance report must state callback overhead explicitly.

## GIL behavior

Because checkpoint-1 RK4 invokes a Python derivative callback, the GIL cannot simply remain released across the whole solve.

Do not claim native speed from moving only RK4 arithmetic into C when callback time dominates.

Future provider performance stages should reduce callback crossings through:

- batched systems;
- native RHS descriptors/kernels;
- specialized PDE/grid operators;
- compiled expression/RHS contracts where justified.

## Python adapter `ode.py`

Conceptual:

```python
def solve_rk4_native_cpu(
    system: FirstOrderSystem,
    *,
    end_time: float,
    steps: int = 256,
) -> ODESolution:
    validate inputs
    times, states = _native.solve_rk4(...)
    validate returned lengths/finiteness
    return ODESolution(times=times, states=states)
```

Keep validation behavior aligned with `solve_rk4`:

- steps >= 1;
- end_time > initial_time;
- derivative dimension mismatch rejected;
- non-finite native result rejected.

## Optional import behavior

Importing core Spectra must not require the native extension.

Preferred behavior:

```text
spectra import -> works
built-in catalog -> works
native provider package absent -> no effect
native provider installed/enabled -> domain factory contributes implementation
```

Within the provider package, unavailable extension should produce a clear provider-unavailable diagnostic rather than partially registering a broken solver.

## Registration transaction

Domain registration must be atomic through existing `DomainRegistry.add_domain/add_domains` semantics.

If native library import/ABI validation fails during registration:

- no solver implementation remains registered;
- no capability marker remains registered;
- previous registry state restored.

## ABI/build identity

Provider should expose durable metadata such as:

```text
provider package version
native ABI version
compiler/build identifier when useful
architecture
```

Do not place volatile memory addresses in provenance.

First ABI version could conceptually be:

```text
spectra.native_cpu.ode.abi = 1
```

## Tests — provider unit

```text
test_native_provider_import_is_optional
test_native_domain_registers_rk4_native_cpu
test_native_solver_not_default_initially
test_native_execution_descriptor_is_cpu_float64
test_native_problem_predicate_accepts_first_order_system
test_invalid_steps_rejected
test_derivative_dimension_mismatch_rejected
test_derivative_exception_propagates_cleanly
```

## Tests — analytical parity

### Exponential

```text
y' = y
y(0)=1
exact y(1)=e
```

Compare reference/native at same steps.

### Harmonic oscillator

Two-state periodic system.

Check state error and energy trend within expected RK4 tolerance.

### Multi-state linear system

Use deterministic matrix coefficients and known/reference solution.

## Convergence gate

Use existing convergence experiment infrastructure.

Expected observed order:

```text
~4
```

Do not promote provider if convergence is inconsistent with declared method order.

## Dispatch gate

Load:

```text
DifferentialEquationsDomain
NativeCpuOdeDomain
```

Then verify:

```text
ode.solve_first_order_with(... implementation_id="rk4.native_cpu")
```

uses the native provider.

Then set requirements/policy:

```text
execution kind = cpu
allow_reference = false
minimum_order = 4
```

and verify normal `ode.solve_first_order` resolves native provider through existing policy.

## Vertical high-level gate

Choose one existing high-level ODE-backed domain, preferably simple mechanics or a small PDE method-of-lines problem.

Test:

```text
reference policy -> solve
native CPU policy -> solve
same high-level domain API/source
compare results within tolerance
tracked provenance records different implementation/backend
```

No edit to the high-level domain is allowed merely to enable native execution.

## Performance benchmark

Report separately:

```text
Python validation/packing
native loop time
Python derivative callback time/estimated share
materialization
total
```

Use several state sizes and step counts.

A result slower than Python reference at small states is acceptable for checkpoint 1 if the architectural provider/ABI path is correct and honestly documented.

## Checkpoint 2 — batched native CPU

Only after checkpoint 1 is green.

Add an explicit batched contract for many independent compatible ODE systems.

Goal:

- amortize boundary overhead;
- allow native threading/SIMD;
- connect directly to experiment batching.

Do not change the single-problem semantic API unnecessarily.

## Checkpoint 3 — native RHS/performance

If Python callback overhead dominates, introduce evidence-driven native RHS mechanisms.

Possible paths:

- supported linear-system descriptor;
- compiled safe expression kernel;
- domain/provider-specific grid RHS;
- batched vectorized callback contract.

Do not put arbitrary Python AST execution into C as an optimization shortcut.

## GPU prerequisite

Do not start GPU provider until:

- native CPU role/provider integration is green;
- buffer ownership is proven;
- provenance/selection works;
- batching contract is understood;
- parity/convergence harness is reusable.

## Files that should not need edits

Native CPU checkpoint should not require edits to:

```text
Maxwell domain
heat domain
chemistry domain
mechanics domain
PDE scientific semantics
Blender backend
Scene primitives
presentation system
```

If those edits are required to select the provider, stop and reassess the solver boundary.

## Exit gate

The first native CPU checkpoint is complete when:

- provider is optional/removable;
- registration is transactional;
- `rk4.native_cpu` appears alongside `rk4.reference`;
- explicit/policy selection works;
- tracked provenance is correct;
- analytical parity passes;
- observed order is ~4;
- one high-level domain switches implementation without source change;
- no unsupported performance claim is made.

The architectural proof matters more than raw speed in this first native checkpoint.