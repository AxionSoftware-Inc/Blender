# Spectra Science — Numerical Backend Validation and Benchmark Protocol

This document defines the acceptance protocol for future native CPU, GPU, and external numerical solver providers.

Performance alone is not sufficient. A faster provider must preserve the numerical/scientific contract before it can become a preferred or default implementation.

## Validation levels

Use four explicit levels.

### Level 0 — Contract smoke

The provider can be discovered, loaded, selected, and invoked without changing scientific-domain code.

Required:

- DomainCatalog provider loading works;
- solver role registration works;
- implementation metadata is complete;
- a supported problem executes;
- an unsupported problem is rejected cleanly;
- returned semantic result type is correct;
- tracked provenance identifies the real implementation/backend/precision.

### Level 1 — Numerical parity

The provider agrees with trusted analytical/reference results within a declared error envelope.

Required before broader scientific use.

### Level 2 — Stability and workload coverage

The provider is exercised over representative state sizes, time horizons, parameter ranges, and repeated/batched execution.

Required before becoming a preferred implementation.

### Level 3 — Production execution readiness

Adds cancellation, robust error classification, memory-pressure handling, device loss/recovery where relevant, packaging/ABI compatibility, and long-running stress tests.

Required before claiming production-ready execution.

## Common ODE validation set

A first-order ODE provider should include at least these problems.

### Constant derivative

```text
y' = c
```

Checks basic time integration and terminal-time correctness.

### Exponential growth/decay

```text
y' = λy
```

Analytical solution exists and is suitable for convergence/error measurements.

### Harmonic oscillator as first-order system

```text
x' = v
v' = -ω²x
```

Checks coupled-state handling and long-term phase/energy behavior.

### Multi-dimensional decoupled system

Use tens to thousands of independent components with known analytical behavior. This is useful for native/vectorized/GPU scaling without introducing complex physics semantics.

### Non-autonomous system

Use explicit time dependence to verify the provider does not assume autonomous systems unless it declares that limitation.

## Fixed-step validation

For fixed-step methods:

- run step refinement;
- measure absolute/relative error;
- estimate observed convergence order;
- compare with declared method order;
- verify deterministic repeatability where promised.

A provider should not become the default if it reports order 4 but consistently behaves as order 1–2 on standard analytical tests.

## Adaptive validation

Adaptive methods require a different protocol.

Use tolerance refinement instead of fixed-step-count convergence:

```text
rtol/atol loose
    ↓
medium
    ↓
tight
```

Measure:

- final solution error;
- accepted steps;
- rejected/internal steps if available;
- function evaluations if available;
- runtime;
- work/error tradeoff.

Changing the caller's `steps` hint alone is not an adaptive convergence study.

## PDE validation

PDE providers built on method-of-lines should separately validate spatial and temporal behavior.

### Spatial operator parity

For regular-grid operators use analytic polynomial fields where finite differences have known results.

Examples:

```text
u = x² + y²      => ∇²u = 4
u = x²+y²+z²     => ∇²u = 6
linear fields    => second derivative = 0
```

### Temporal integration parity

Use zero/static RHS problems to isolate time integration.

### Diffusion

Check:

- no spontaneous growth for standard positive diffusion;
- qualitative smoothing;
- conservation where boundary semantics imply it;
- reference comparison over short intervals.

### Wave equations

Check:

- zero state remains zero;
- expected propagation speed on simple cases;
- energy trend over short/medium horizons.

### Schrödinger-like complex PDEs

Check:

- normalization/probability mass;
- simple free/constant states;
- reference complex-state parity.

## Domain-specific invariants

Native/GPU providers should be validated through existing domain diagnostics when possible rather than backend-specific checks.

Examples:

- fluid maximum divergence;
- kinetic energy/enstrophy trends;
- Maxwell Gauss residuals;
- EM energy;
- quantum probability mass/continuity residual;
- mechanics total energy in conservative fields;
- elastodynamic rigid translation strain/stress = 0;
- reaction-network conservation constraints where applicable.

This validates the provider through scientific semantics instead of only array equality.

## Precision matrix

Every provider should declare and test each supported precision separately.

Suggested matrix:

```text
float32
float64
complex64
complex128
```

Only test dtypes the provider genuinely supports.

For each precision record:

- analytical error;
- reference error;
- invariant residual;
- runtime;
- memory usage.

Do not compare float32 and float64 using identical absolute tolerances blindly.

## State-size matrix

For first-order dense systems, a useful initial benchmark matrix is:

```text
8
32
128
512
2k
8k
32k
128k components
```

Stop before memory/runtime becomes unreasonable for the target backend.

GPU launch overhead will often make very small systems slower than Python/native CPU. That is expected and should be measured, not hidden.

## Batch-size matrix

For providers advertising batching, test:

```text
1
2
4
8
16
32
64
128 cases
```

Use identical-shape independent problems first.

Measure throughput as well as latency:

```text
cases/second
state-elements/second
```

## Timing protocol

Separate timings into phases where possible:

```text
semantic packing
host allocation
host→device upload
kernel/integration
device→host readback
semantic materialization
total end-to-end
```

Run warmups before timed GPU/native measurements.

Report median and at least one spread statistic (for example p10/p90 or min/max across controlled repeats). Avoid quoting a single lucky run.

## Memory protocol

Record:

- host bytes allocated;
- device bytes allocated;
- peak workspace;
- persistent workspace after prepare;
- bytes uploaded/read back;
- whether allocation is reused between runs.

A provider that is faster but leaks device memory is not acceptable.

## Repeated-run stress

At minimum:

```text
100 repeated small solves
20 repeated medium solves
5 repeated large solves
```

where practical.

Verify:

- memory returns to steady state;
- result parity remains stable;
- no provider-owned resource count grows monotonically;
- cleanup is idempotent.

## Failure/fallback tests

Explicitly test:

- unsupported problem shape;
- unsupported precision;
- allocation failure simulation if possible;
- missing/unavailable device;
- provider initialization failure;
- non-finite numerical output;
- policy fallback to the next compatible implementation.

A fallback must never silently change problem semantics.

## Reproducibility tests

For deterministic providers:

- same problem + same environment should reproduce within the promised bitwise/numerical envelope;
- environment snapshot/fingerprint should identify implementation and policy changes;
- traced experiment artifacts should preserve selected implementation IDs and execution summaries.

GPU floating-point reductions may not be bitwise deterministic. If so, document the numerical reproducibility guarantee instead of claiming bitwise identity.

## Benchmark comparison table

A provider report should include a compact table like:

| workload | implementation | precision | total ms | solve ms | upload ms | readback ms | peak memory | error |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ODE 512 | rk4.reference | f64 | ... | ... | n/a | n/a | ... | ... |
| ODE 512 | rk4.native_cpu | f64 | ... | ... | n/a | n/a | ... | ... |
| ODE 512 | rk4.cuda | f32 | ... | ... | ... | ... | ... | ... |

For batch tests add throughput.

## Promotion criteria

### May be registered

Level 0 contract smoke passes.

### May be recommended for explicit opt-in

Level 1 numerical parity passes for its declared support envelope.

### May be selected by an automatic preferred policy

Levels 1–2 pass, fallback behavior is validated, provenance is correct, and the provider has a meaningful performance benefit in its target workload range.

### May become global default

Only after broad regression coverage shows that the change does not surprise high-level scientific domains and the fallback/packaging story is mature.

Reference implementations should remain available even after a faster default exists.

## First native-provider acceptance target

For a native CPU RK4 provider, the first milestone should be:

- same `ode.first_order` role;
- same `ODESolution` result contract;
- analytical tests pass;
- observed fourth-order convergence;
- execution trace reports native CPU backend;
- state sizes through at least several thousand values;
- repeated-run memory stable;
- measurable speedup over Python reference for medium/large systems.

Only after that should GPU complexity be introduced.
