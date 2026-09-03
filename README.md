# Spectra Science

Spectra Science is a **renderer-independent scientific computation and visualization engine** under active pre-alpha development.

The original Blender-addon prototype is preserved on:

```text
legacy/pre-semantic-core-2026-08-30
```

`main` is the semantic-engine architecture. New work must build on the semantic/capability model rather than the legacy addon design.

## Read first

Start with the documentation index:

- `docs/README.md`
- `docs/SYSTEM_ARCHITECTURE_MAP.md`
- `docs/DOMAIN_SYSTEM.md`
- `docs/DOMAIN_CATALOG.md`
- `docs/SOLVERS_AND_EXPERIMENTS.md`
- `docs/PREMIUM_PRESENTATION_SYSTEM.md`
- `docs/PRODUCT_WORKFLOWS.md`
- `docs/POST_VALIDATION_IMPLEMENTATION_PLAN.md`

Subsystem-specific documents for numerical providers, Blender, plugins, projects, security, performance, and scientific/multiphysics foundations are indexed in `docs/README.md`.

## Product thesis

Spectra is not a collection of Blender science buttons. Scientific meaning exists before renderer objects.

```text
scientific intent
    -> domain semantics
    -> reusable computation capabilities
    -> numerical execution roles
    -> semantic fields / trajectories / solutions
    -> visualization compiler
    -> generic Scene + Timeline
    -> presentation policy
    -> renderer backend
```

Possible authoring surfaces include formulas, Python APIs, declarative documents, simulation/data inputs, project files, Blender UI, standalone clients, and later AI compilation. Possible outputs include Blender, realtime/WebGPU clients, saved Scene/project documents, images/video, interactive lessons, reports, and remote/headless rendering.

The engine must remain useful if Blender disappears tomorrow.

## Core rule

**Core is not calculus, quantum physics, relativity, CFD, chemistry, Blender, CUDA, WebGPU, UI state, or a plugin marketplace.**

Core owns reusable cross-domain/cross-renderer abstractions such as:

- vectors/colors/transforms/coordinates/bounds;
- units, quantities, dimensions, typed constants;
- restricted expression infrastructure;
- generic Scene primitives/resources;
- Timeline/interpolation;
- Scene composition and serialization;
- domain/backend contracts.

A new scientific subject is not sufficient reason to modify Core.

## Domain architecture

`DomainRegistry` is runtime authority. `DomainCatalog` auto-discovers built-in `...Domain` classes, probes their real `provide()` registrations, indexes capability ownership, and computes dependency closure.

Domains consume stable versioned capabilities rather than importing another subject's private algorithms.

The architecture now spans more than one hundred auto-discovered scientific/numerical domains and several hundred capability providers. Examples include:

```text
mathematics
calculus
linear algebra
tensor algebra
tensor fields
differential geometry
geodesics
probability / statistics
graph theory
ODE / PDE 1D / 2D / 3D
complex and coupled PDEs
transport / diffusion / Poisson
mechanics / particles / waves
fluid kinematics and reference incompressible flow
elasticity / elastodynamics
heat conduction / thermoelasticity
electromagnetism / Maxwell
quantum mechanics / Schrödinger 1D/2D/3D
special/general relativity
chemistry / reaction kinetics / reaction-diffusion
multiphysics coupling
experiments / convergence / sensitivity / uncertainty / calibration
```

The exact provider graph is generated from runtime registration rather than duplicated in a central capability manifest.

## Composition rule

High-level science should reuse lower-level capabilities.

Examples already represented in the architecture:

```text
linear algebra + probability
    -> finite-dimensional quantum

complex fields + integration
    -> spatial quantum wavefunctions

ODE role
    -> method-of-lines PDE
    -> diffusion / waves / Schrödinger / heat / chemistry

Poisson + grid operators
    -> fluid pressure projection
    -> streamfunction flow
    -> electrostatic potential
    -> gravitational potential

tensor algebra + matrix inverse
    -> differential geometry curvature
    -> general relativity

Christoffel symbols + ODE role
    -> geodesics

elasticity + vector PDE
    -> elastodynamics

heat conduction + elasticity
    -> thermoelasticity / thermoelastodynamics

Maxwell fields + Lorentz force + mechanics
    -> charged-particle trajectories

reaction network + coupled PDE
    -> reaction-diffusion

reaction enthalpy
    -> volumetric heat source

J · E
    -> electrothermal heating
```

New domains should normally compose existing capabilities before introducing new algorithms.

## Numerical execution architecture

Scientific domains no longer need to name a concrete time integrator such as RK4.

They consume stable numerical roles:

```text
scientific problem
      ↓
ode.solve_first_order
      ↓
NumericalSolverRegistry
      ↓
reference / native CPU / GPU / external implementation
```

Reference implementations currently include fixed-step RK4 and Heun/RK2, plus an adaptive Dormand-Prince/RK45 provider in the current post-baseline development batch.

Solver selection can use:

- execution kind (`python`, `cpu`, `gpu`, `external`);
- precision;
- minimum order;
- fixed/adaptive behavior;
- tags;
- priority;
- semantic problem compatibility;
- ordered fallback policies.

The goal is that native/GPU providers can replace execution without rewriting physics, chemistry, PDE, mechanics, or visualization code.

See `docs/SOLVERS_AND_EXPERIMENTS.md`, `docs/NATIVE_NUMERICAL_BACKENDS.md`, and `docs/PERFORMANCE_BUDGETS.md`.

## Experiments and reproducibility

The current post-baseline numerical platform adds generic support for:

- deterministic Cartesian parameter sweeps;
- batched experiment execution;
- solver comparison;
- convergence studies;
- unit-aware local sensitivity;
- deterministic weighted uncertainty propagation;
- candidate-grid calibration;
- ranking and Pareto fronts;
- renderer-neutral experiment views;
- per-case numerical execution traces;
- scientific environment snapshots and SHA-256 fingerprints;
- schema-versioned JSON experiment artifacts.

Environment fingerprints account for loaded domain/capability versions, solver implementations, execution metadata, defaults, and active solver policies.

## Mathematics and geometry foundation

Current foundations include:

- expression-backed and callable real/complex functions;
- 2D/3D scalar, vector, and time-dependent fields;
- parametric curves/surfaces;
- derivative/integration/gradient/divergence/curl/Jacobian;
- real/complex vectors and matrices;
- determinant/inverse/Hermitian tools/eigensystems;
- arbitrary-rank tensors and tensor fields;
- metric tensor fields;
- index raising/lowering;
- Christoffel symbols;
- Riemann/Ricci/scalar curvature;
- geodesic semantics and explicit projection views.

Metrics may be positive-definite or indefinite. Renderer code must never guess how higher-dimensional coordinates should be projected.

## PDE and numerical-field foundation

Current computation layers include:

- uniform 1D/2D/3D grids;
- fixed / periodic / zero-gradient boundaries;
- finite-difference derivatives and Laplacians;
- real and complex method-of-lines systems;
- scalar/vector second-order PDEs;
- coupled multi-component PDEs;
- advection and advection-diffusion;
- Poisson/elliptic reference solvers;
- grid integrals and conservation diagnostics;
- bilinear/trilinear grid-to-field adapters;
- time-series grid-to-field adapters;
- explicit 3D slices into existing `Surface` visualization.

Reference solvers are architectural/reference implementations, not claims of production CFD/FDTD/FEA fidelity.

## Physics and multiphysics foundation

Architecture proofs/foundations include:

- Newtonian mechanics and particle systems;
- 1D/2D/3D diffusion;
- scalar waves and acoustics;
- Coulomb/electrostatic/gravitational potential fields;
- field lines and particle-field dynamics;
- incompressible-flow reference solvers and diagnostics;
- elasticity and elastodynamics;
- heat conduction and thermoelastic coupling;
- finite-dimensional and spatial quantum mechanics;
- Schrödinger evolution in 1D/2D/3D;
- quantum probability current/continuity diagnostics;
- special relativity;
- Schwarzschild/general-relativity foundation;
- time-domain Maxwell reference evolution;
- Maxwell source/Gauss/energy/Poynting diagnostics;
- electrothermal coupling;
- reaction networks, reaction-diffusion, and thermochemical heating.

These are foundations and composition proofs, not claims that every scientific field is feature-complete.

## Generic Scene vocabulary

Renderer-neutral primitives include:

- `Point`, `PointCloud`;
- `Polyline`;
- `Surface`, `Region`;
- `VectorGlyph`, `VectorGlyphSet`;
- `TextLabel`, `Group`;
- `Camera`, `Light`.

A Scene also owns materials, coordinate frame, active camera, and Timeline.

Dense scientific data must remain batched. Many particles should normally be one `PointCloud`; large vector fields should normally be one `VectorGlyphSet`.

## Presentation architecture

Scientific visualization and premium presentation are separate layers.

```text
semantic result
    -> explicit/default scientific view
    -> base Scene + scientific Timeline
    -> PresentationIntent
    -> enriched Scene/presentation resources
    -> Blender / WebGPU / future renderer
```

The presentation layer owns communication choices such as camera, color scales, legends, axes, annotations, lighting intent, reveal order, and quality/display sampling. It must not alter numerical data or solver resolution.

The premium presentation runtime itself is currently a design target for the post-validation phases; do not report the design documents as already implemented functionality.

See `docs/PREMIUM_PRESENTATION_SYSTEM.md`, `docs/VISUAL_DESIGN_SYSTEM.md`, and `docs/BLENDER_PREMIUM_ACCEPTANCE.md`.

## Animation and composition

Spectra owns scientific time:

```text
Scene + Timeline
    -> Scene.sample(t)
    -> static Scene snapshot
    -> backend.apply(snapshot)
```

Backends do not own scientific timing.

Dynamic arrays such as particle positions, polyline points, surface vertices, and vector-field arrays can be animated while preserving stable topology/IDs for incremental backends.

Presentation time/reveal/camera motion is intended to compose over scientific time without changing physical interpretation.

## Projects, plugins, and product surfaces

The architecture now has design contracts for:

- renderer-independent project/study state;
- model/result/view/presentation invalidation;
- external resource/data ingestion;
- a curated future `spectra.sdk`;
- third-party plugin packaging/discovery;
- API/schema compatibility;
- structured diagnostics;
- remote/HPC execution;
- trust/security boundaries.

These are design contracts until their runtime milestones are implemented and verified.

A `.blend` file may be a useful derived renderer artifact, but the long-term scientific source of truth should be a Spectra project/semantic model independent from Blender.

## Scene documents

Current Scene schema:

```text
spectra.scene v4
```

Readers retain compatibility with versions 1–3. Schema changes must remain deliberate and backward compatibility must not be silently broken.

## Backends

### MemoryBackend

Renderer-free reference backend.

### BlenderBackend

Reference Blender adapter with lazy `bpy`/`mathutils` imports. Renderer SDKs do not enter Core or scientific domains.

### IncrementalBlenderBackend

Preserves stable Spectra IDs as stable Blender objects and updates common native data buffers in place when topology is unchanged.

Dense mapping includes:

```text
PointCloud     -> one Blender mesh object
VectorGlyphSet -> one Blender Curve representation
```

`BlenderTimelineController` maps Blender transport frames to Spectra engine time while Spectra remains the source of timeline semantics.

## Verified baseline

The last completed local/native validation milestone is commit:

```text
acb9e056326177fac49cc57b202ca80cca5090a7
```

Results:

```text
compileall spectra: PASS
pytest:             224 passed
DomainCatalog:      PASS
Blender 5.2 LTS:    native smoke PASS
```

Native Blender validation included:

- static curve/surface/material/light/camera creation;
- animated wave geometry updates;
- animated E/B `VectorGlyphSet` updates;
- stable Blender object/datablock identity;
- topology fallback;
- cleanup/orphan checks;
- 10k batched PointCloud/VectorGlyphSet behavior;
- 121-frame leak test.

Example native PointCloud reference measurements from that machine:

```text
10k create: ~199 ms
10k update: ~96–97 ms
```

These are Blender/Python-backend reference numbers, not GPU-solver benchmarks.

## Current post-baseline batch

`main` has moved substantially beyond the verified 224-test baseline with solver interchangeability, policies, adaptive RK45, experiments, reproducibility, artifacts, tracing, and related refactors.

**Do not claim the current `main` head is green until the next full local validation is run.**

GPU/native numerical-provider implementation has not yet been validated or promoted.

Documentation/specification work after the runtime batch does not itself require Blender/GPU validation and should be interpreted according to `docs/CAPABILITY_MATURITY_MODEL.md`.

GitHub Actions remains intentionally absent. Do not recreate it unless explicitly requested.

## Forbidden regressions

Do not:

- import renderer SDKs into Core/scientific domains;
- import CUDA/Metal/WebGPU execution details into physics/chemistry semantics;
- implement new science directly as Blender operators/objects;
- recreate giant subject-specific utility modules;
- make UI state the scientific model;
- make AI the deterministic engine core;
- duplicate math/solver algorithms inside physics when capabilities already exist;
- hardcode RK4 or another concrete solver in high-level domains when a stable solver role exists;
- expand dense data into thousands of Scene/backend objects;
- let a backend invent missing scientific semantics;
- silently downgrade numerical precision;
- silently fall back to a solver with different problem semantics;
- auto-install/execute arbitrary plugin code from untrusted project files;
- store generated releases/build artifacts in source control.

## Repository policy

- `main` — current semantic engine.
- `legacy/pre-semantic-core-2026-08-30` — preserved old addon.
- generated caches/renders/builds/releases do not belong in source control.

## Near-term roadmap

After the current post-baseline numerical/experiment batch is validated, the highest-value product sequence is:

```text
1. renderer-neutral presentation semantics
2. presentation composer
3. quantitative color scales + legends
4. five canonical premium scientific scenes
5. Blender premium presentation adapter
6. dense/Geometry Nodes presentation optimizations
7. curated public SDK
8. external plugin discovery
9. renderer-independent project format
```

A parallel numerical-performance track can then proceed through:

```text
1. native CPU first-order provider
2. typed numerical buffers
3. batched native execution
4. GPU batched ODE/grid operators
5. increasingly device-resident PDE pipelines
6. remote/HPC execution for larger workloads
```

Performance work follows numerical parity first, speed second. Product milestones and exit criteria are detailed in `docs/PRODUCT_MILESTONES.md`.

## Success criterion

A new scientific idea should usually require:

- new semantics or composition of existing semantics;
- reuse of existing computation capabilities;
- an existing or interchangeable numerical execution role;
- compilation into generic visual primitives;
- optional reusable presentation policy;
- tests;

and **not** require another renderer-specific, UI-specific, or device-specific scientific subsystem.

Spectra should become a scientific computation, project, and presentation engine with Blender support—not a Blender addon that accumulated scientific features.
