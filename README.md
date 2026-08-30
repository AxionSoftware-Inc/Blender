# Spectra Science

Spectra Science is being rebuilt as a **renderer-independent scientific visualization engine** for mathematics, physics, statistics, probability, and future scientific domains.

It is **not** a collection of Blender buttons for derivatives, integrals, limits, graphs, and isolated physics demos. Blender is the first high-quality renderer/backend, not the scientific model and not the identity of the engine.

> **Status:** architectural reset / pre-alpha. The original Blender-addon prototype is preserved unchanged on `legacy/pre-semantic-core-2026-08-30`.

This README is a source-of-truth document. A future developer, agent, or ChatGPT session should read it before adding features.

---

## 1. Product thesis

The long-term product should accept scientific intent from one or more authoring surfaces and compile it into a renderer-independent scientific scene.

Possible authoring inputs:

- formulas and equations;
- Python API calls;
- declarative scene documents;
- lesson/storyboard templates;
- data or simulation results;
- natural language compiled by an AI layer.

Possible outputs:

- Blender scenes and cinematic renders;
- realtime WebGPU/desktop/mobile visualization;
- interactive scientific scenes;
- images and video;
- reusable lesson timelines;
- remote/headless render jobs.

The central pipeline is:

```text
scientific intent
    -> scientific/domain semantics
    -> reusable computation capabilities
    -> visualization compiler
    -> generic Spectra Scene
    -> engine-owned Timeline
    -> static Scene sample at time t
    -> renderer backend
```

The core must remain useful if Blender disappears tomorrow.

---

## 2. Why the old architecture was reset

The original prototype successfully proved that Blender can generate useful math/science scenes. It also exposed a scalability problem: scientific meaning, numerical evaluation, Blender objects, materials, collections, frame state, HUD text, UI settings, and animation were tightly coupled.

The old growth pattern was effectively:

```text
new scientific topic
    -> new Blender operator
    -> new Blender objects/materials
    -> new custom animation code
    -> more UI state
```

That can produce many features while the engine itself becomes harder to extend. Physics makes the problem worse because fields, trajectories, particles, waves, differential equations, tensors, coordinate transforms, constraints, and simulations would each create another renderer-specific subsystem.

The new direction is:

```text
scientific meaning
    -> semantic model
    -> generic visual vocabulary
    -> engine animation
    -> backend
```

The previous implementation remains useful as prototype/reference material, but its architectural coupling must not be copied into `main`.

---

## 3. The most important architectural rule

**Core is not calculus. Core is not physics. Core is not Blender.**

Core owns only abstractions that remain useful across many unrelated scientific subjects and renderers.

Scientific knowledge lives in pluggable domains.

```text
Spectra Core
├── values / transforms / units / coordinates
├── expression infrastructure
├── generic Scene primitives
├── Timeline / interpolation
├── Scene serialization
├── presentation-independent resources
└── stable domain/backend contracts

DomainRegistry / capability graph
├── mathematics
├── calculus
├── probability
├── probability.continuous
├── statistics
├── linear_algebra
├── differential_equations
├── graph_theory
└── physics
    ├── mechanics
    ├── particles
    ├── electromagnetism
    └── quantum

Scene
├── primitives
├── materials
├── coordinate frame
├── active camera
└── timeline

Backends
├── MemoryBackend
├── BlenderBackend
└── future WebGPU / other renderers
```

Adding a new subject is **not** enough reason to modify Core.

A useful test before changing Core is:

> If this scientific subject disappeared tomorrow, would this abstraction still make sense for several unrelated domains?

If the answer is no, keep it in a domain.

---

## 4. Domain composition instead of duplicated science

Domains publish stable capabilities through `DomainRegistry`. Other domains consume those capabilities instead of importing or copying implementation internals.

Examples already represented in the codebase:

### Quantum composition

```text
linear algebra
    ComplexVector / ComplexMatrix
    normalization
    Hermitian checks
    operator application
    quadratic forms

probability
    distributions

        -> physics.quantum
           QuantumState
           QuantumObservable
           measurement distribution
           expectation value
```

Quantum does not own a second matrix library or a second probability implementation.

### Continuous probability composition

```text
mathematics.Function1D
        -> calculus.integrate
        -> probability.continuous
           PDF / CDF / interval probability
```

Probability does not reimplement integration.

### Mechanics composition

```text
differential_equations.FirstOrderSystem
        + ode.solve_rk4
        -> mechanics
           particle problem
           trajectory
```

### Multi-particle composition

```text
ODE solver
    -> physics.particles
       N-body state
       ParticleSystemTrajectory
    -> one animated PointCloud Scene node
```

### Electromagnetism composition

```text
mathematics.VectorField3D
        -> Coulomb-law field
        -> VectorGlyphSet
        -> renderer backend
```

The same field representation can later be reused by gravity, magnetic fields, fluid velocity, PDE solutions, or newly invented physical models.

---

## 5. Capability contracts and versioning

A domain depends on a **capability contract**, not another domain's private implementation.

Examples:

- `mathematics.function1d`
- `mathematics.vector_field3d`
- `calculus.integrate`
- `probability.discrete_distribution`
- `linear_algebra.normalize_complex`
- `ode.solve_rk4`
- `physics.particles.solve_system`

Capabilities carry versions. A consumer may require a minimum version without knowing how the provider is implemented.

This allows a capability implementation to move later from pure Python to NumPy, SciPy, Rust, C++, SIMD, GPU compute, or another solver while dependent domains keep the same contract.

`DomainRegistry.add_domains(...)` accepts modules in arbitrary order and resolves required capabilities automatically.

Domain registration is transactional: if one domain fails during registration, partial semantic types/capabilities/visualizers are rolled back. Batch registration is also atomic.

This is required if Spectra eventually loads dozens or hundreds of domains.

---

## 6. Current Core

### Basic values

Current renderer-independent values include:

- `Vec2`
- `Vec3`
- `Color`
- `Quaternion`
- `Transform3D`
- `CoordinateFrame3D`
- dimensional `Unit` / `Quantity`

`Transform3D` owns translation, rotation, scale, point/vector application, and camera-style `look_at` behavior.

Scientific coordinates remain distinct from backend/world coordinates. A `Scene` carries a coordinate frame; a backend maps it into its native space.

### Expressions

The expression layer uses a restricted Python AST whitelist with approved functions/constants rather than unrestricted user `eval` input.

It supports deterministic formula evaluation without importing Blender.

### Scene primitives

Current renderer-independent primitive vocabulary includes:

- `Point`
- `PointCloud`
- `Polyline`
- `Surface`
- `Region`
- `VectorGlyph`
- `VectorGlyphSet`
- `TextLabel`
- `Group`
- `Camera`
- `Light`

This list should grow only when a genuinely reusable visual abstraction is needed.

### Batched primitives are intentional

Dense scientific data must not become one Python Scene object per sample.

`PointCloud` stores many points/particles in one Scene node.

`VectorGlyphSet` stores many vector arrows in one Scene node.

Example:

```text
100 x 100 x 100 vector field
```

must not imply one million Scene primitives. It should remain one batched `VectorGlyphSet` whose arrays can map to native/GPU instancing.

Likewise, a many-particle simulation should normally animate one `PointCloud`, not create thousands of Scene nodes.

---

## 7. Scene materials and lighting

Presentation intent is renderer-independent.

A `Scene` owns reusable `Material` resources. A primitive may reference one through `material_id`.

Current material contract includes:

- base color;
- `unlit` or `lit` shading intent;
- metallic;
- roughness;
- emission color/strength;
- double-sided intent.

`Light` is also a generic Scene primitive with ambient/directional/point/spot intent.

These are **not** Blender node trees or Blender light objects. Blender maps them to native resources inside its backend.

Missing material references fail when the generic Scene is constructed rather than becoming hidden renderer errors.

---

## 8. Animation belongs to Spectra

Blender frames are not the source of scientific truth.

The engine owns:

- `Keyframe`
- `Track`
- `Timeline`
- interpolation
- nested property paths
- timeline validation
- sampling at arbitrary time

Supported interpolation currently includes step, linear, and smooth interpolation for relevant numeric/vector/color/quaternion/tuple values.

Examples include:

- point movement;
- particle positions;
- curve draw/reveal through `trim_start` / `trim_end`;
- opacity fades;
- camera transforms;
- vector/color transitions.

The important runtime contract is:

```text
animated semantic scene
    -> Scene + Timeline
    -> Scene.sample(t)
    -> static Scene snapshot
    -> backend.apply(snapshot)
```

A backend is therefore not expected to understand calculus, probability, mechanics, or scientific time semantics.

`BackendSession` drives any backend from the same Spectra timeline.

---

## 9. Presentation helpers are not scientific domains

Presentation transformations such as `staggered_reveal()` operate on an existing generic Scene.

They do not belong inside calculus, probability, graph theory, or physics.

This means the same reveal/fade/draw composition can be applied to graphs, functions, probability plots, trajectories, fields, or future scientific modules without changing their domain semantics.

Camera and light primitives are presentation controls and are excluded from automatic reveal effects.

---

## 10. Bounds and automatic camera framing

Spectra distinguishes two useful spaces:

- **Scene-local scientific bounds** — appropriate for generic camera framing;
- **parent/world-mapped bounds** — after applying the Scene coordinate frame.

`Bounds3D`, `scene_local_bounds()`, and `scene_bounds()` provide this distinction.

`fit_camera_to_scene()` and `with_fitted_camera()` create renderer-independent cameras using conservative bounds. This keeps framing logic outside Blender and allows the same scientific composition to be framed similarly by other renderers.

Cameras, groups, and lights do not enlarge scientific content bounds.

---

## 11. Scene document format

The current document schema is:

```text
spectra.scene version 4
```

It serializes generic Scene state including:

- primitives;
- transforms;
- batched point/vector data;
- timeline/keyframes/interpolation;
- coordinate frame;
- active camera;
- material resources;
- material references;
- lights.

Readers intentionally retain support for earlier scene versions 1, 2, and 3.

Schema compatibility should be treated deliberately. Do not silently break saved scientific scenes when adding a new resource.

The document format is important for future:

- saved projects;
- remote rendering;
- CLI jobs;
- web/realtime clients;
- AI-generated scenes;
- backend-independent interchange.

---

## 12. Current scientific domains

### Mathematics

Currently includes foundation for:

- intervals and rectangular domains;
- `Function1D`;
- `Function2D`;
- parametric 3D curves;
- parametric 3D surfaces;
- scalar/vector fields;
- regular sampling grids.

Visualization examples:

```text
Function1D -> Polyline
Function2D -> indexed Surface
ParametricCurve3D -> Polyline
ParametricSurface3D -> Surface
VectorField3D -> batched VectorGlyphSet
```

### Calculus

Currently includes reusable numerical foundation such as:

- derivative sampling;
- tangent samples;
- numerical integration.

Calculus is a domain, not privileged Core functionality.

### Probability

Discrete probability includes outcomes/distributions, expectation, and variance.

Continuous probability is a dependent subdomain using `Function1D` and the calculus integration capability for normalization/CDF/interval probability.

### Statistics

Includes dataset/summary/histogram semantics and reuses probability capabilities for empirical distributions.

### Linear algebra

Includes real/complex vectors and matrices, inner products, normalization, matrix-vector application, adjoint/Hermitian checks, and quadratic forms.

### Differential equations

Contains a deterministic fixed-step RK4 reference implementation behind a stable capability contract.

The current solver is a correctness/reference foundation, not a commitment to pure-Python RK4 forever.

### Graph theory

Includes graphs, edges, layouts, neighbor traversal, unweighted shortest path, and renderer-independent visualization.

This domain is intentionally useful as proof that Spectra is not secretly a continuous-calculus engine.

### Physics

Current slices include:

- Newtonian single-particle mechanics;
- multi-particle systems;
- Coulomb electric fields;
- quantum states/observables/expectation values.

These are architecture proofs and reusable foundations, not claims that the domains are scientifically complete.

---

## 13. Backend contract

Backends consume static generic Scene snapshots.

A backend implements approximately:

```text
create(scene) -> native handle
apply(handle, scene)
destroy(handle)
```

Backend capabilities explicitly declare which primitive/resource types are supported.

A backend may reject unsupported content before renderer-specific work begins.

### MemoryBackend

`MemoryBackend` is a renderer-free reference backend used to prove the backend/session boundary without Blender.

### BlenderBackend

A first real Blender backend now exists under:

```text
spectra/backends/blender/
```

Critical rule:

> `bpy` must never be imported into Core or scientific domains.

`BlenderBackend` lazy-loads `bpy`/`mathutils` only when native operations (`create/apply/destroy`) actually execute. Importing `BlenderBackend` in ordinary Python therefore remains valid.

The first static vertical slice supports:

- Point;
- Polyline;
- Surface;
- Region;
- single VectorGlyph;
- TextLabel;
- organizational Group empty;
- Camera;
- Light;
- Material mapping;
- Scene coordinate-frame root mapping.

Current Blender backend intentionally rebuilds its backend-owned collection on `apply()`. That is a reference implementation, not the final animation-performance strategy.

`PointCloud` and `VectorGlyphSet` are deliberately **not yet advertised by BlenderBackend** until they are mapped to batched/native instanced Blender geometry. They must not be implemented by creating one Blender object per instance.

Group children are not currently parented under Blender group empties because Core does not yet define inherited Group transforms. A backend must not invent semantics that Core does not own.

---

## 14. Forbidden architectural regressions

These rules are deliberate.

### Do not put `bpy` into Core or domains

No Blender imports in:

- `spectra.core`;
- mathematics;
- calculus;
- probability/statistics;
- physics;
- generic visualization compilers.

### Do not add scientific concepts as renderer-specific features

Bad:

```text
IntegralFeature -> create Blender mesh/material/operator
```

Correct direction:

```text
integral semantics
    -> generic region/curve/label/timeline
    -> Scene
    -> backend
```

### Do not create another giant tools module

Do not recreate files equivalent to old giant `calculus_tools.py` or a future giant `physics_tools.py`.

### Do not make UI state the scientific model

A Blender panel, web form, or desktop UI is an authoring surface. It reads/writes semantic objects/documents; it does not own scientific truth.

### Do not make AI the core

AI may compile intent into deterministic Spectra semantics later. The engine, validation, computation contracts, Scene compiler, and backends must work without AI.

### Do not optimize for feature count

Ten new buttons are less valuable than one abstraction that makes the next hundred concepts cheap.

### Do not expand batched data into thousands of Scene/backend objects

Large fields, particles, samples, and repeated glyphs require batch/instancing abstractions.

### Do not store generated release ZIPs in source control

Use release/build artifacts outside the source tree.

---

## 15. Performance direction

The current Python implementations are reference implementations chosen to stabilize semantics and contracts.

Performance-sensitive capabilities may later move behind the same contracts to:

- NumPy;
- SciPy;
- Rust;
- C++;
- SIMD;
- GPU compute;
- specialized native solvers.

The scientific domains should not need to be rewritten when that happens.

For visualization, prefer:

- compact semantic objects;
- batch primitives;
- native instancing;
- renderer-side buffers;
- incremental backend updates;
- lazy/streamed data where required.

Do not prematurely optimize by leaking renderer structures back into scientific semantics.

---

## 16. Testing status

The repository contains a growing plain-Python test suite for:

- expressions/functions;
- domain dependencies/versioning/transactions;
- calculus;
- probability/statistics;
- linear algebra/quantum;
- ODE mechanics and particle systems;
- graph theory;
- visualization compilers;
- animation/timeline;
- serialization compatibility;
- bounds/camera framing;
- batched primitives;
- materials/lights;
- backend contracts;
- Blender lazy import boundary.

**Do not claim the complete current suite is green yet.**

Local full `pytest` execution was intentionally deferred while the user's local agent was busy. When local verification resumes, run the complete suite and fix failures before declaring a stable milestone.

The previous GitHub Actions workflow was intentionally removed from `main` at the user's request. Do not recreate it unless explicitly requested later.

---

## 17. Repository policy

- `main` — new semantic-engine architecture only.
- `legacy/pre-semantic-core-2026-08-30` — complete old addon snapshot before reset.
- Generated ZIPs/renders/caches/build artifacts do not belong in `main`.
- Experimental renderer/domain work should remain cleanly separated from universal Core abstractions.

---

## 18. What counts as a good new feature

Before implementation, answer:

1. What is the scientific meaning?
2. Does an existing domain object already express it?
3. Which existing capability can it reuse?
4. Does it really require a new domain capability?
5. Which generic visual primitives express it?
6. Can dense data use an existing batch primitive?
7. Which Timeline properties are needed?
8. Can it be tested without Blender?
9. Can another backend consume the resulting Scene?
10. Does this truly require a Core change?

If implementation starts with “create this Blender object/operator/panel,” it is probably at the wrong layer.

---

## 19. Near-term development order

Unless a newer architectural decision explicitly supersedes this roadmap:

1. stabilize the first BlenderBackend static vertical slice;
2. add Blender-native/batched support for `PointCloud` and `VectorGlyphSet` without object explosion;
3. run the full plain-Python test suite locally and fix every failure;
4. run a Blender smoke test using a generic Function/Surface/Camera/Light Scene;
5. make Blender `apply()` incremental instead of full collection rebuild where performance requires it;
6. rebuild selected calculus visualizations (integral/derivative/etc.) as semantic compositions rather than old addon features;
7. deepen physics through reusable math capabilities (fields, waves, ODE/PDE, operators) rather than renderer-specific demos;
8. only after contracts stabilize, build richer authoring UI/CLI/AI layers.

---

## 20. Continuation instructions for another agent/chat

If the current conversation is unavailable:

1. Read this README.
2. Read `docs/DOMAIN_SYSTEM.md`.
3. Inspect latest `main` rather than assuming this README is newer than code.
4. Do **not** resume development from the legacy calculus addon.
5. Keep `spectra.core` free of renderer SDKs and subject-specific knowledge.
6. Reuse domain capabilities instead of copying algorithms.
7. Use `DomainRegistry.add_domains(...)` for dependency-resolved loading.
8. Compile semantics into generic Scene primitives before renderer code.
9. Keep Timeline ownership in Spectra.
10. Preserve Scene schema backward compatibility intentionally.
11. Prefer batched primitives for dense scientific data.
12. Never implement `PointCloud`/`VectorGlyphSet` by generating one Blender object per instance.
13. Update this README when an architectural decision materially changes.
14. Local full tests are still pending until explicitly completed; do not invent a green result.
15. GitHub Actions is intentionally absent.

When uncertain, optimize for:

**generality, composability, scientific meaning, deterministic contracts, renderer independence, testability, and the cost of adding the 100th scientific concept.**

---

## Success criterion

Spectra succeeds architecturally when a new scientific idea usually requires:

- new semantics or composition of existing semantics;
- reuse of existing computation capabilities;
- compilation into existing generic visual primitives;
- tests;

and **does not** require another renderer-specific subsystem.

The target is a scientific scene engine with Blender support — not a Blender addon that accumulated scientific features.
