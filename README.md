# Spectra Science

Spectra Science is a **renderer-independent scientific computation and visualization engine** under active pre-alpha development.

The original Blender-addon prototype is preserved on:

```text
legacy/pre-semantic-core-2026-08-30
```

`main` is the semantic-engine architecture. New work must build on the semantic/capability model rather than the legacy addon design.

## Read first

Start with:

- `docs/CURRENT_STATUS.md`
- `docs/README.md`
- `docs/SYSTEM_ARCHITECTURE_MAP.md`
- `docs/DOMAIN_SYSTEM.md`
- `docs/DOMAIN_CATALOG.md`
- `docs/SOLVERS_AND_EXPERIMENTS.md`
- `docs/PREMIUM_PRESENTATION_SYSTEM.md`
- `docs/PRODUCT_WORKFLOWS.md`

Subsystem-specific documents for numerical providers, Blender, plugins, projects, security, performance, presentation, SDK, and scientific/multiphysics foundations are indexed in `docs/README.md`.

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
- generic Scene primitives/resources and visual attributes;
- Timeline/interpolation;
- Scene composition and serialization;
- domain/backend contracts.

A new scientific subject is not sufficient reason to modify Core.

## Domain architecture

`DomainRegistry` is runtime authority. `DomainCatalog` auto-discovers built-in `...Domain` classes, probes their real `provide()` registrations, indexes capability ownership, and computes dependency closure.

Domains consume stable versioned capabilities rather than importing another subject's private algorithms.

At the current verified baseline the catalog reports:

```text
119 domains
467 capability providers
```

Examples span:

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
presentation / project / plugin / SDK-supporting domains
```

The provider graph is generated from runtime registration rather than duplicated in a central capability manifest.

## Composition rule

High-level science should reuse lower-level capabilities.

Examples represented in the architecture:

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

Scientific domains consume stable numerical roles rather than naming one concrete integrator.

```text
scientific problem
      ↓
ode.solve_first_order
      ↓
NumericalSolverRegistry
      ↓
reference / native CPU / future GPU / external implementation
```

Verified reference implementations include fixed-step RK4 and Heun/RK2 plus adaptive Dormand–Prince/RK45.

Solver selection can use:

- execution kind (`python`, `cpu`, `gpu`, `external`);
- precision;
- minimum order;
- fixed/adaptive behavior;
- tags;
- priority;
- semantic problem compatibility;
- ordered fallback policies.

The first `rk4.native_cpu` provider-role proof is also present and validated through the same registry/provenance path. This establishes provider interchangeability; it is not yet a claim that all numerical execution is native or faster than reference Python.

See `docs/SOLVERS_AND_EXPERIMENTS.md`, `docs/NATIVE_NUMERICAL_BACKENDS.md`, and `docs/PERFORMANCE_BUDGETS.md`.

## Experiments and reproducibility

The verified numerical platform includes generic support for:

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

A Scene also owns materials, coordinate frame, active camera, Timeline, and generic `VisualAttribute` data attached to compatible primitives.

Dense scientific data must remain batched. Many particles should normally be one `PointCloud`; large vector fields should normally be one `VectorGlyphSet`.

## Presentation runtime

Scientific visualization and presentation remain separate layers:

```text
semantic result
    -> explicit/default scientific view
    -> base Scene + scientific Timeline
    -> PresentationIntent
    -> enriched Scene/presentation resources
    -> Blender / future WebGPU / other renderer
```

The presentation layer owns communication choices such as camera, color policy, annotations, lighting intent, reveal order, and display quality. It must not alter numerical data or solver resolution.

The first renderer-neutral presentation runtime is now implemented and validated, including policy/preset resolution, deterministic presentation resources, Scene-local camera fitting, and scientific/presentation animation ownership rules.

More advanced presentation depth—continuous quantitative legends, richer screen-space layout, volume presentation, and renderer-specific premium effects—remains future work.

See `docs/PREMIUM_PRESENTATION_SYSTEM.md`, `docs/PRESENTATION_COMPOSER_PIPELINE.md`, and `docs/BLENDER_PREMIUM_ACCEPTANCE.md`.

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

Presentation tracks compose with scientific time under explicit conflict rules; presentation does not silently override a scientific track for the same target/property.

## Projects, plugins, SDK, and product surfaces

The first runtime foundations now exist for:

- renderer-independent project documents/state;
- curated `spectra.sdk` facade;
- plugin descriptors/registry/catalog composition;
- API/schema compatibility foundations;
- reuse of existing numerical/reproducibility artifacts.

These are verified foundation layers, not yet a complete plugin marketplace, collaboration server, remote/HPC product, or polished standalone application.

A `.blend` file remains a derived renderer artifact rather than the long-term scientific source of truth.

## Scene documents

Current Scene schema:

```text
spectra.scene v5
```

Scene v5 adds generic visual attributes. Readers retain compatibility with earlier supported Scene versions according to the serialization contract. Schema changes must remain deliberate and backward compatibility must not be silently broken.

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

## Current verified baseline

The current fully reported local/native validation milestone is:

```text
b9ca6b017cac83f45cc3864a88e219c848c12fc8
```

Results:

```text
compileall spectra: PASS
pytest:             276 passed
initial failures:   0
DomainCatalog:      PASS — 119 domains / 467 providers
numerical/provenance/solver registry: PASS
presentation / Scene v5 / VisualAttribute: PASS
SDK / plugin / project layers: PASS
native CPU RK4 provider: PASS
Blender 5.2 LTS targeted smoke: PASS
repo: clean and synchronized
```

Targeted Blender validation included:

- static scene mapping;
- animated wave geometry;
- animated E/B `VectorGlyphSet` updates;
- stable Blender object/datablock identity;
- 10k batched `PointCloud` and `VectorGlyphSet` behavior;
- one native representation per dense batch rather than 10k Blender objects;
- 100-frame leak test;
- cleanup/orphan checks.

Reported reference measurement from that validation run:

```text
create:          ~170.49 ms
combined update: ~89.95 ms
```

These are commit/machine/run-specific Blender backend reference numbers, not GPU numerical benchmarks.

GitHub Actions remains intentionally absent. Do not recreate it unless explicitly requested.

## Still not production-grade

The verified architecture should not be confused with industrial completeness.

Examples still outside current production scope include:

- industrial CFD/RANS/LES/AMR and very large production meshes;
- full FEM/contact/plasticity/fracture/shell/beam workflows;
- production RF/FDTD/PML/dispersive-material workflows;
- quantum chemistry/DFT/many-body solvers;
- real GPU numerical provider/device-resident PDE execution;
- complete premium volume/screen-space scientific presentation;
- mature external plugin marketplace/distribution;
- collaborative project server and remote/HPC product runtime;
- standalone/WebGPU production UI.

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

Further work should branch from the `b9ca6b0...` verified baseline in bounded checkpoints.

High-value presentation/render track:

```text
1. richer quantitative color/legend runtime
2. Blender visual-attribute/material realization
3. canonical premium scientific showcase scenes
4. dense/Geometry Nodes optimization where measured evidence requires it
5. richer layout/annotation/volume presentation
```

Numerical-performance track:

```text
1. move beyond the native-provider proof to real native execution where useful
2. typed numerical buffers and batching
3. GPU provider and batched ODE/grid operators
4. increasingly device-resident PDE pipelines
5. remote/HPC execution for larger workloads
```

Product track:

```text
1. strengthen SDK/plugin/project contracts from real usage
2. headless/CLI/export workflows
3. standalone/WebGPU product surface
4. later collaboration/remote worker integration
```

Performance work follows numerical parity first, speed second. Product milestones and exit criteria are detailed in `docs/PRODUCT_MILESTONES.md`.

## Success criterion

A new scientific idea should usually require:

- new semantics or composition of existing semantics;
- reuse of existing computation capabilities;
- an existing or interchangeable numerical execution role;
- compilation into generic visual primitives/attributes;
- optional reusable presentation policy;
- tests;

and **not** require another renderer-specific, UI-specific, or device-specific scientific subsystem.

Spectra should become a scientific computation, project, and presentation engine with Blender support—not a Blender addon that accumulated scientific features.
