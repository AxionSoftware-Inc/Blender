# Spectra Science

Spectra Science is a **renderer-independent scientific visualization engine** under active architectural rebuild.

> Status: pre-alpha / semantic-engine reset. The complete old Blender-addon prototype is preserved on `legacy/pre-semantic-core-2026-08-30`.

This README is the project source of truth. Read it, `docs/DOMAIN_SYSTEM.md`, `docs/DOMAIN_CATALOG.md`, and `docs/BLENDER_BACKEND.md` before extending the engine.

## Product thesis

Spectra is not a Blender calculus addon. Scientific meaning must exist before renderer objects.

```text
scientific intent
    -> domain semantics
    -> reusable computation capabilities
    -> visualization compiler
    -> generic Scene + Timeline
    -> Scene.sample(t)
    -> renderer backend
```

Possible inputs include formulas, Python APIs, declarative documents, simulations, datasets, lesson templates, and later AI-compiled natural language. Possible outputs include Blender renders, realtime viewers, interactive lessons, images/video, saved Scene documents, and remote render jobs.

The engine must remain useful if Blender disappears tomorrow.

## Core rule

**Core is not calculus, probability, quantum physics, or Blender.**

Core owns only abstractions useful across many unrelated subjects/renderers:

- values, transforms, coordinates, bounds;
- dimensions, units, quantities, typed physical constants;
- safe expression infrastructure;
- generic Scene primitives/resources;
- Timeline/interpolation;
- Scene composition/namespaces;
- Scene serialization;
- domain/backend contracts.

Scientific knowledge lives in pluggable domains.

```text
DomainRegistry / DomainCatalog
├── mathematics
├── calculus
├── linear_algebra
├── probability
├── probability.continuous
├── statistics
├── graph_theory
├── differential_equations
├── partial_differential_equations
├── partial_differential_equations.complex
└── physics
    ├── mechanics
    ├── particles
    ├── diffusion
    ├── waves
    ├── electromagnetism
    ├── quantum
    ├── quantum.spatial
    └── quantum.schrodinger1d
```

A new subject is not by itself a reason to modify Core.

## Capability composition

Domains publish versioned capabilities. Consumers depend on contracts, not provider internals.

Examples already represented in code:

```text
linear algebra + probability
    -> finite-dimensional quantum

ComplexFunction1D + calculus.integrate + continuous probability
    -> normalized spatial quantum wavefunction

ODE RK4
    -> real PDE method-of-lines
    -> diffusion physics

ODE RK4
    -> complex PDE adapter
    -> 1D time-dependent Schrodinger physics

VectorField3D / TimeDependentVectorField3D
    -> electrostatics / EM waves
    -> VectorGlyphSet + Timeline

ODE RK4
    -> mechanics / multi-particle trajectories
    -> Polyline / PointCloud
```

`DomainRegistry` is runtime authority and registration is transactional. `DomainCatalog` discovers providers and computes missing dependency closure, so a product layer can request only a high-level domain such as `physics.quantum.schrodinger1d`.

## Mathematics foundation

Current mathematics semantics include:

- `Interval`, rectangular domains;
- `Function1D` — safe expression-backed real function;
- `CallableFunction1D` — callable/native/plugin-backed real function;
- `RealFunction1D` — structural contract consumed by calculus/compiler code;
- `ComplexFunction1D`;
- `Function2D`;
- parametric 3D curves/surfaces;
- scalar/vector fields;
- time-dependent scalar/vector fields;
- regular grids and field-view animation semantics.

Calculus currently provides derivative/tangent sampling, Simpson integration over any `RealFunction1D`, gradient, divergence, and curl.

Linear algebra includes real/complex vectors and matrices, normalization, inner products, matrix-vector application, adjoints, Hermitian checks, identities, and quadratic forms.

Probability includes discrete distributions plus a continuous subdomain that reuses calculus integration for normalization/CDF/interval probability. Statistics includes datasets, summary statistics, histograms, and empirical distributions.

Graph theory exists deliberately as proof that Spectra is not secretly a calculus-only engine.

## Differential equations and physics

`differential_equations` contains a deterministic fixed-step RK4 reference solver behind stable `ode.*` contracts.

`partial_differential_equations` adds uniform 1D spatial discretization, boundary-aware second derivatives, scalar method-of-lines problems/solutions, and animated profile visualization while reusing the ODE solver.

`partial_differential_equations.complex` encodes complex state as real/imaginary ODE buffers and reuses the same solver stack.

Current physics architecture slices include:

- Newtonian single-particle mechanics;
- multi-particle systems;
- diffusion/heat-like scalar evolution;
- harmonic waves/superposition;
- Coulomb electric fields;
- plane electromagnetic waves;
- finite-dimensional quantum states/observables;
- normalized spatial wavefunctions and position distributions;
- 1D time-dependent Schrodinger evolution.

These are reusable foundations and architecture proofs, not claims of scientific completeness.

## Units and physical constants

`Dimension`, `Unit`, and `Quantity` support dimensional conversion and arithmetic. Compatible additions convert units; multiplication/division/integer powers carry dimensions.

Typed constants in `spectra/core/constants.py` currently include speed of light, elementary charge, Planck constant, reduced Planck constant, Boltzmann constant, and Coulomb constant.

Physics may cache SI floats in hot loops, but typed quantities remain the source of dimensional meaning.

## Scene vocabulary

Current generic primitives include:

- `Point`, `PointCloud`;
- `Polyline`;
- `Surface`, `Region`;
- `VectorGlyph`, `VectorGlyphSet`;
- `TextLabel`, `Group`;
- `Camera`, `Light`.

A Scene also owns materials, coordinate frame, active camera, and Timeline.

Dense data must stay batched. A million vector samples should normally remain one `VectorGlyphSet`; many particles should normally remain one `PointCloud`.

## Animation and composition

Spectra owns scientific time:

```text
Scene + Timeline
    -> Scene.sample(t)
    -> static Scene
    -> backend.apply(...)
```

Backends must not become the source of scientific timing.

Current animation supports numeric/vector/color/quaternion/tuple interpolation, transforms, opacity, curve reveal, particle arrays, dynamic curve points, dynamic surfaces, vector-field arrays, and cameras.

`spectra.core.composition` provides namespacing and Scene composition so independently-authored domain Scenes can be combined without coordinating IDs manually.

## Scene documents

Current document schema is `spectra.scene` version 4. Readers retain versions 1-3 for backward compatibility.

The format stores generic primitives, transforms, batched data, timelines, coordinate frame, camera, materials, material references, and lights. It is intended for saved projects, CLI/remote rendering, realtime clients, and AI-generated scenes.

## Backend contract

Backends consume static generic Scene snapshots:

```text
create(scene) -> handle
apply(handle, scene)
destroy(handle)
```

### MemoryBackend

Renderer-free reference backend.

### BlenderBackend

Reference Blender backend. `bpy`/`mathutils` are lazy dependencies and must never enter Core or scientific domains.

It maps Point, PointCloud, Polyline, Surface, Region, VectorGlyph, VectorGlyphSet, TextLabel, Group, Camera, Light, and Material.

Dense mappings are batched:

```text
PointCloud     -> one Blender mesh object
VectorGlyphSet -> one Blender Curve object with many splines
```

### IncrementalBlenderBackend

Performance-oriented adapter that preserves stable Spectra IDs as stable Blender objects and updates common buffers in place when possible.

Current fast paths include Point positions, PointCloud positions, Polyline points, Surface vertices, VectorGlyphSet origins/vectors, and transform/visibility-only changes.

`BlenderTimelineController` maps Blender playback frames to Spectra engine time and drives `BackendSession.seek(t)`. Blender supplies transport controls; Spectra owns the timeline semantics.

See `docs/BLENDER_BACKEND.md`.

## Forbidden regressions

Do not:

- import Blender SDKs into Core/domains/generic compilers;
- implement new science directly as Blender operators/objects;
- recreate giant `calculus_tools.py` / `physics_tools.py` modules;
- make UI state the scientific model;
- make AI the deterministic engine core;
- expand dense scientific data into thousands of Scene/backend objects;
- let backends invent scientific semantics Core does not own;
- store generated release ZIPs/build artifacts in source control.

Correct direction:

```text
scientific semantics
    -> reusable capabilities
    -> generic primitives/timeline
    -> Scene
    -> backend
```

## Performance direction

Current Python numerical implementations are reference implementations used to stabilize contracts. They may later be replaced behind the same capability names by NumPy, SciPy, Rust, C++, SIMD, GPU compute, or specialized solvers.

Prefer compact semantics, batch primitives, native buffers/instancing, incremental updates, and lazy/streamed data when needed.

## Testing status

The repository has a growing plain-Python test suite covering expressions/functions, registry/catalog dependency resolution, calculus/vector calculus, probability/statistics, linear algebra/quantum, ODE/PDE/complex-PDE composition, diffusion, Schrodinger evolution, graph theory, units/constants, Scene composition, animation, serialization, bounds/camera, batched primitives, backend contracts, Blender lazy import, and incremental-backend logic.

**Do not claim the complete suite is green yet.** Local full `pytest` execution is intentionally deferred while the user's local agent is busy. Run the complete suite and fix failures before declaring a stable milestone.

The previous GitHub Actions workflow was intentionally removed from `main` at the user's request. Do not recreate it unless explicitly requested later.

## Repository policy

- `main` — new semantic-engine architecture only.
- `legacy/pre-semantic-core-2026-08-30` — complete old addon snapshot.
- generated ZIPs/renders/caches/build artifacts do not belong in `main`.

## Near-term order

1. Keep strengthening universal scientific contracts without renderer leakage.
2. Add physics by composing existing math/field/ODE/PDE/operator capabilities.
3. Keep DomainCatalog metadata synchronized with new bundled capabilities.
4. Keep Blender incremental/batched paths free of object explosion.
5. Keep README/docs synchronized with architecture.
6. When local testing resumes, run full `pytest` and fix every failure.
7. Run real Blender smoke tests for static, wave, EM, particle, surface, and quantum/PDE scenes.
8. Validate create/apply/destroy cleanup and timeline scrubbing.
9. Build richer UI/CLI/AI authoring only after contracts/runtime behavior stabilize.

Existing Blender examples include:

```text
examples/blender_smoke.py
examples/blender_wave_animation.py
examples/blender_em_wave_animation.py
```

## Continuation instructions

If this conversation is unavailable:

1. Read this README.
2. Read `docs/DOMAIN_SYSTEM.md`, `docs/DOMAIN_CATALOG.md`, and `docs/BLENDER_BACKEND.md`.
3. Inspect latest `main`; code may be newer than docs.
4. Never resume from the legacy addon architecture.
5. Keep Core renderer-independent and subject-neutral.
6. Reuse versioned capabilities rather than copying algorithms.
7. Use DomainCatalog for discovery and DomainRegistry as runtime authority.
8. Compile scientific semantics into generic Scene primitives before backend code.
9. Keep Timeline ownership in Spectra.
10. Preserve Scene schema compatibility deliberately.
11. Prefer batches for dense data.
12. Never map PointCloud/VectorGlyphSet to one Blender object per instance.
13. Update docs when architecture materially changes.
14. Local full tests remain pending until actually run.
15. GitHub Actions is intentionally absent.

When uncertain, optimize for **generality, composability, scientific meaning, deterministic contracts, renderer independence, testability, and the cost of adding the 100th scientific concept.**

## Success criterion

A new scientific idea should usually require new semantics or composition, reuse existing computation, compile into existing generic visual primitives, and add tests — **without creating another renderer-specific subsystem**.

Spectra should become a scientific scene engine with Blender support, not a Blender addon that accumulated scientific features.
