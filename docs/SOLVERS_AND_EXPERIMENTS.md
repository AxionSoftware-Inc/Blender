# Spectra Science — Solvers, Experiments, and Reproducibility

This document describes the numerical execution and experiment layer underneath scientific domains. Core and scientific semantics remain independent from any particular CPU/GPU solver technology.

## Two separate mechanisms

```text
DomainCatalog / capabilities
    -> discover and load provider domains

NumericalSolverRegistry
    -> choose one loaded implementation for a stable solver role at runtime
```

A capability answers **what provider functionality must exist**. A solver role answers **which loaded implementation executes a numerical contract**.

The first-order ODE role is:

```text
ode.first_order
```

Built-in implementations currently include:

- `rk4.reference` — fixed-step fourth-order RK4, default;
- `heun.reference` — optional fixed-step second-order Heun/RK2;
- `rk45.reference` — optional adaptive Dormand–Prince 5(4).

Legacy `ode.solve_rk4` remains available for compatibility and reference validation.

## Role-dispatched scientific composition

High-level domains depend on:

```text
ode.first_order_system
ode.solve_first_order
```

rather than a concrete RK method.

```text
native/GPU/adaptive first-order implementation
                  ↓
          ode.first_order role
                  ↓
   method-of-lines / mechanics / fields
                  ↓
wave / heat / chemistry / fluid / quantum / solids / Maxwell
```

`ode.solve_first_order` is problem-aware and policy-aware. Changing the runtime implementation does not require editing physics or PDE code.

Explicit dispatch is also available:

- `ode.solve_first_order_with` — exact implementation ID;
- `ode.solve_first_order_selected` — one-off requirements;
- tracked variants preserve the selected execution provenance.

## Loading optional implementations

A solver-provider domain exposes an ordinary capability and registers its runtime implementation.

Examples:

```text
ode.first_order.heun_reference
    -> differential_equations.reference_solvers
    -> ode.first_order / heun.reference

ode.first_order.rk45_reference
    -> differential_equations.adaptive_reference
    -> ode.first_order / rk45.reference
```

Capability-driven loading is supported:

```python
catalog.load_capabilities(
    registry,
    ("ode.first_order.rk45_reference",),
)
```

A future native provider follows the same pattern:

```text
normal discoverable capability
        ↓
provider domain dependency closure
        ↓
registry.register_numerical_solver(
    role="ode.first_order",
    implementation_id="rk4.native_gpu",
    ...
)
```

No central backend switch statement is required.

## Execution metadata and requirements

Each implementation can describe:

- execution kind: `python`, `cpu`, `gpu`, or `external`;
- backend identifier;
- precision;
- optional device identifier;
- in-place support;
- batch support;
- priority;
- tags;
- optional semantic `supports_problem` predicate.

Selection requirements can constrain:

- execution kind;
- precision;
- minimum order;
- adaptive/fixed behavior;
- reference implementations;
- required tags.

Problem-aware selection filters by both requirements and the semantic problem predicate.

## Ordered solver policies

A `NumericalSolverPolicy` stores ordered requirement rules plus optional fallback to the exact default implementation.

Conceptually:

```text
1. prefer compatible GPU non-reference
2. otherwise prefer compatible CPU non-reference
3. otherwise use default reference solver
```

The high-level `ode.solve_first_order` dispatch applies the active policy automatically. Scientific domains do not contain `if CUDA`, `if Metal`, or backend-specific fallback code.

Policies are transactional registry state. Failed domain registration rolls policy mutations back together with capabilities and solver implementations.

## Numerical provenance

Tracked runs distinguish **requested work** from **executed work**.

A `NumericalRunRecord` can contain:

- method or composed pipeline identity;
- start/end time;
- accepted/executed step count;
- requested step count or adaptive initial-step hint;
- state size;
- semantic tags;
- solver role and implementation ID;
- execution kind/backend/precision.

For fixed-step solvers:

```text
requested_steps == accepted steps
fixed_step_size is defined
```

For adaptive solvers:

```text
requested_steps = initial step-size hint
steps           = accepted integration steps
average_step_size is available
fixed_step_size is intentionally undefined
```

A tracked 3D method-of-lines run composes:

```text
method-of-lines scalar 3D
        +
actual policy-selected ODE method
        ↓
PDE pipeline provenance
```

The PDE trace propagates the selected solver ID, backend, precision, requested hint, and actual accepted step count.

## Parameter sweeps and batching

The base `experiments` domain provides deterministic Cartesian sweeps:

```text
ParameterAxis × ParameterAxis × ...
        ↓
stable ParameterCase IDs
        ↓
evaluator
        ↓
unit-aware metrics
        ↓
ExperimentResult
```

Failures can raise immediately or be recorded per case.

`experiments.batching` groups stable case sequences for vectorized/native/GPU evaluators without assuming a particular compute API.

## Per-case numerical execution traces

`experiments.tracing` allows a case evaluator to return its scientific output together with one or more `NumericalRunRecord` values.

This supports workflows such as:

```text
one experiment case
    -> heat solve
    -> elasticity solve
    -> particle solve
    -> metrics
```

while preserving every numerical run used by that case.

The trace records selected implementations, so two cases may legitimately use different compatible solvers under a problem-aware policy.

## Solver comparison and convergence

`experiments.compare_solvers` executes one problem through multiple implementations of the same role and applies common metrics.

`experiments.convergence` performs step-refinement convergence studies for **fixed-step** implementations. It computes observed order from error ratios and compares it with declared method order.

Adaptive solvers are deliberately rejected by the fixed-step convergence API because their `steps` argument is only a step-size hint. Adaptive tolerance/refinement studies should use a separate tolerance-based experiment contract rather than pretending requested step counts are fixed discretizations.

## Experiment analysis

`experiments.analysis` provides generic result analysis:

- deterministic metric ranking;
- best-case selection;
- minimize/maximize objectives;
- multi-objective Pareto fronts.

These operate on experiment metrics and do not know any particular scientific domain.

## Local sensitivity

`experiments.sensitivity` provides unit-aware central finite-difference sensitivities.

For each parameter/metric pair it records:

- baseline parameter in SI;
- baseline response in SI;
- raw SI derivative;
- dimensionless normalized sensitivity when defined.

This makes the same analysis usable for material properties, reaction rates, geometry parameters, field strengths, and other domains.

## Deterministic uncertainty propagation

`experiments.uncertainty` uses weighted discrete parameter samples and deterministic Cartesian scenarios.

It computes unit-aware metric:

- expectation;
- variance;
- standard deviation.

The first uncertainty foundation is intentionally deterministic and seed-free. Monte Carlo, Latin hypercube, or quasi-random providers can later use compatible result semantics.

## Calibration

`experiments.calibration` performs deterministic candidate-grid fitting using weighted least-squares residuals in SI units.

It returns:

- all candidate results;
- failed candidates when recording is enabled;
- the best parameter set;
- normalized observation residuals;
- final objective value.

This establishes a calibration semantic contract without coupling Spectra to one optimizer implementation.

## Renderer-independent experiment views

`experiments.views` makes visualization explicit rather than asking a backend to infer scientific intent.

Current views include:

- metric response series → `PointCloud + Polyline`;
- Pareto front → batched `PointCloud`;
- convergence plot → `Polyline + PointCloud`;
- sensitivity stems → `Polyline + TextLabel + PointCloud`.

They use the same generic Scene vocabulary already validated by the Blender backend and are equally usable by future WebGPU or other renderers.

## Reproducibility snapshots

`spectra.reproducibility.capture_environment(registry)` records:

- domain names and versions;
- capability names, versions, and providers;
- solver roles and implementation IDs;
- method IDs;
- execution kind/backend/precision;
- defaults, priority, and tags;
- active ordered solver policies and their requirement rules.

The canonical payload supports deterministic `to_dict/from_dict` and SHA-256 fingerprinting.

Changing a solver policy therefore changes the environment fingerprint even when the loaded implementation inventory is unchanged.

The environment fingerprint complements rather than replaces source-control commit IDs, input hashes, compiler/device metadata, and other packaging provenance.

## Durable experiment artifacts

`experiments.artifacts` creates schema-versioned JSON-friendly experiment summaries.

Artifacts preserve:

- parameter axes and values;
- quantity/unit metadata;
- metric definitions and values;
- recorded failures;
- full scientific environment snapshot and fingerprint;
- optional per-case numerical run summaries;
- arbitrary string metadata.

Arbitrary runtime solver outputs are intentionally not serialized by this layer. Durable scientific summaries and runtime Python/native objects remain separate contracts.

Artifacts have their own canonical SHA-256 fingerprint and validate the embedded environment fingerprint during loading.

## Extension rule for native/GPU solvers

A new numerical implementation should normally:

1. live in a provider domain/plugin rather than Core;
2. depend on the stable solver role it implements;
3. expose a normal capability for catalog loading;
4. register a unique implementation ID;
5. provide method and execution metadata;
6. declare problem compatibility when its support is limited;
7. preserve the common role call contract;
8. participate in comparison/convergence or other verification studies;
9. expose tracked provenance;
10. avoid leaking backend-specific concepts into scientific domains.

The intended boundary is:

```text
scientific semantics remain stable
          ↓
solver role remains stable
          ↓
policy selects compatible execution
          ↓
Python reference / native CPU / GPU / external implementation
```

This is the execution foundation Spectra needs for high-performance scientific backends without sacrificing reproducibility or modularity.
