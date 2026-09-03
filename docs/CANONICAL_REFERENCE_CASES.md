# Spectra Science — Canonical Reference Cases

This document defines a stable suite of small analytical and medium-size numerical cases for future regression, solver parity, performance, presentation, and renderer validation.

The goal is to avoid every new backend/provider choosing unrelated ad-hoc examples.

Reference cases are not all required at every checkpoint. Each subsystem selects the relevant subset.

## Principles

A good reference case should be:

- deterministic;
- small enough to run routinely when appropriate;
- analytically or independently checkable where possible;
- representative of a reusable engine contract;
- renderer-independent at the scientific level;
- useful for comparing reference/native/GPU providers;
- explicit about units, grid sizes, tolerances, and expected invariants.

## Tier 0 — pure analytical micro-cases

These are intended for correctness and contract validation.

### ODE exponential growth

```text
y' = y
y(0) = 1
t ∈ [0,1]
exact: y(t)=e^t
```

Use for:

- RK4/Heun/RK45 correctness;
- convergence order;
- provenance;
- solver comparison;
- adaptive/fixed dispatch.

Metrics:

```text
final absolute error
accepted steps
requested step hint
observed order for fixed methods
```

### ODE harmonic oscillator

First-order form of:

```text
x'' + x = 0
```

Use for:

- vector state;
- phase-space behavior;
- long-ish conservation trend;
- native/GPU parity.

Metrics:

```text
position/velocity error
energy drift
```

### Scalar field gradient

```text
f(x,y,z)=x+2y-3z
∇f=(1,2,-3)
```

Use for 3D gradient operator parity.

### Vector field divergence/curl

Example:

```text
v=(-y,x,0)
div(v)=0
curl(v)=(0,0,2)
```

Use for:

- vector calculus;
- field adapters;
- fluid kinematics;
- GPU grid-operator parity.

### Unit-cube integral

Constant scalar field over unit cube.

Expected integral equals scalar value.

Use for:

- GridIntegrals3D;
- conservation diagnostics;
- native reduction kernels.

## Tier 1 — small grid PDE cases

### Stationary constant scalar PDE

Constant state with zero RHS.

Expected state remains unchanged exactly up to floating representation.

Use for:

- method-of-lines dispatch;
- adaptive/fixed solver substitution;
- history/field bridges;
- tracked provenance.

### 3D diffusion constant state

Uniform scalar field, periodic or zero-gradient boundary.

Expected uniform field remains uniform.

Use for:

- Laplacian correctness;
- diffusion solver parity;
- GPU stencil implementation.

### 3D linear advection

Choose a field/function with known translation under constant velocity and a grid/boundary setup suitable for deterministic reference comparison.

Use for:

- upwind operator parity;
- transport pipelines;
- CFL diagnostics.

### 3D Poisson manufactured solution

Choose a simple smooth potential such as a separable polynomial/trigonometric field where the Laplacian and boundary values are known.

Use for:

- Poisson convergence;
- electrostatic/gravitational adapters;
- native linear-solver providers later.

## Tier 2 — physics composition cases

### Electrostatic point/known-source field

A small domain with either a manufactured charge density or a simple point-source deposition case.

Validate:

```text
potential symmetry
E = -∇V
Gauss residual trend
field direction
```

Presentation target:

```text
potential slice + field vectors + field lines
```

### Gravitational potential symmetry

Analogous small mass-source case.

Validate:

```text
potential sign/convention
g = -∇Φ
symmetry
```

### Uniform Maxwell field

Periodic constant E/B with zero curls/sources.

Expected fields remain constant.

Use for:

- Maxwell time solver;
- E/B history-to-field bridge;
- divergence/energy diagnostics;
- VectorGlyphSet animation identity.

### Current-driven Maxwell micro-case

Uniform current density with simple source setup where the expected initial E derivative is known:

```text
∂E/∂t = -J/ε0
```

Use for source/unit/provenance validation.

### Charged particle in uniform magnetic field

Expected circular/helical trajectory depending initial velocity.

Use for:

- Lorentz force;
- field-particle bridge;
- mechanics solver interchangeability.

Metrics:

```text
radius/frequency error
speed conservation
```

### Rigid elastodynamic translation

Periodic homogeneous solid with uniform initial velocity and no strain.

Expected:

```text
velocity constant
strain=0
stress=0
kinetic energy constant
```

Use for vector second-order PDE/elastodynamics parity.

### Uniform heat source

Homogeneous material, spatially uniform heating and compatible boundary conditions.

Expected:

```text
ΔT = q t / (ρ cp)
```

Use for thermal units and heat solver parity.

### Uniform thermal expansion

Uniform temperature increase.

Expected thermal strain known; free body produces no stress, constrained constitutive case produces predictable stress.

Use for thermoelastic coupling.

### Reaction A -> B

Simple first-order or fixed-rate reaction with analytical/well-mixed behavior.

Use for:

- ReactionNetwork;
- ODE solver interchangeability;
- reaction-diffusion limiting cases;
- thermochemical heat sign.

### Free constant quantum state

Constant wavefunction under conditions where spatial derivatives vanish.

Expected:

```text
probability density constant
probability current = 0
continuity residual = 0
```

Use for Schrödinger/quantum-current composition.

## Tier 3 — reference visualization scenes

These cases validate generic Scene composition and presentation, not numerical performance only.

### Wave polyline

Use existing animated-wave style case.

Validate:

- dynamic Polyline points;
- stable primitive/native identity;
- camera framing;
- reveal + scientific playback composition.

### Maxwell vector scene

E/B VectorGlyphSets.

Validate:

- batched representation;
- two-scale/vector legend handling;
- presentation resource ownership;
- animated vector updates.

### Elastodynamic point cloud

Deformed lattice as animated PointCloud.

Validate:

- one batched representation;
- displacement color/legend later;
- incremental positions.

### Scalar slice surface

Temperature/potential/probability-density slice.

Validate:

- quantitative color scale;
- legend range;
- unlit-vs-lit material policy;
- stable Surface topology.

### Geodesic bundle

Several geodesics in an explicit projected view.

Validate:

- projection semantics;
- axes labels;
- camera policy;
- multiple Polyline batching/object behavior where applicable.

## Tier 4 — performance shapes

These are data sizes/layouts, not necessarily full scientific problems.

### PointCloud sizes

```text
1k
10k
100k
1M (future renderer/native target)
```

Measure separately:

```text
semantic construction
Scene apply/create
incremental update
memory
object count
```

### VectorGlyphSet sizes

```text
1k
10k
100k
```

Measure:

- object count;
- curve/instance count;
- update time;
- presentation color/scale overhead.

### Scalar grid sizes

```text
16^3
32^3
64^3
128^3
256^3 future GPU target
```

Measure numerical kernels independently:

- Laplacian;
- gradient;
- divergence;
- simple diffusion steps;
- host-device transfer where applicable.

### Batched ODE

Independent scalar/vector systems:

```text
10
100
1k
10k
```

Use for native/GPU batch crossover measurement.

## Tier 5 — experiment-system reference cases

### One-parameter sweep

Exponential-growth rate or simple material parameter.

Validate:

- deterministic case IDs;
- metrics;
- artifact serialization;
- environment fingerprint;
- per-case trace.

### Two-objective Pareto set

Use a synthetic deterministic design table with known dominated/non-dominated points.

Validate ranking/Pareto view.

### Sensitivity analytical function

Example:

```text
response = a*x^2
```

with known derivative.

Validate raw and normalized sensitivity.

### Weighted uncertainty

Small discrete distribution with manually calculable mean/variance.

Validate deterministic uncertainty propagation.

### Calibration

Simple one-parameter model with known best candidate.

Validate least-squares ranking and residual reporting.

## Reference-case metadata

Each executable reference case should eventually have machine-readable metadata conceptually containing:

```text
case_id
subject
version
required capabilities
parameters/units
expected invariants
reference tolerances
recommended solver policy
presentation target if any
performance tier if any
```

Do not hardcode all validation tolerances globally. Tolerance depends on solver/order/grid/precision.

## Precision matrix

Future native/GPU validation should explicitly test supported precision:

```text
float64 reference
float64 native if supported
float32 GPU/native where declared
```

A provider advertising float32 should be compared against an appropriate float32 error envelope, not silently held to arbitrary float64 tolerances.

## Performance reporting

Always separate:

```text
setup/packing
kernel/solve
transfer
materialization
Scene compile
renderer create
renderer incremental update
final render
```

This prevents a fast kernel with expensive transfer from being reported as universally faster.

## Promotion rule

A native/GPU provider should not become default because it wins one benchmark.

Promotion requires:

- correctness/parity across relevant reference cases;
- convergence behavior where applicable;
- provenance correctness;
- stable problem-compatibility boundaries;
- memory/resource safety;
- demonstrated performance benefit on its declared workload class.

## Presentation use

Canonical presentation scenes should reuse these reference scientific cases where possible so numerical correctness and visual quality are not tested on unrelated data.

`SHOWCASE_SCENARIOS.md` may use larger/more visually compelling variants, but the underlying scientific interpretation should remain compatible with the reference cases.

## Success criterion

Reference Python, native CPU, GPU, Blender, and future WebGPU paths should be compared on a shared vocabulary of deterministic cases rather than each subsystem inventing its own unverifiable demo.
