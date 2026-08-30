# Spectra Science

Spectra Science is a **renderer-independent scientific visualization engine** for mathematics, physics, and other scientific domains.

The project is deliberately **not** being developed as a growing collection of Blender buttons. Blender is intended to be one renderer/backend of Spectra, not the owner of scientific meaning, simulation state, animation timing, or scene structure.

> Status: architectural rebuild / pre-alpha. The complete previous Blender-addon prototype is preserved on `legacy/pre-semantic-core-2026-08-30`.

Read this README together with [`docs/DOMAIN_SYSTEM.md`](docs/DOMAIN_SYSTEM.md). These files are the source of truth for future contributors and future ChatGPT/Codex sessions.

---

## One-sentence architecture

```text
scientific semantics
    -> versioned domain capability graph
    -> renderer-independent visualization compiler
    -> generic Scene + Timeline
    -> Scene.sample(t)
    -> Blender / WebGPU / Unreal / another backend
```

A renderer should never need to know what a derivative, probability distribution, Hermitian observable, electric field, or differential equation means.

It receives generic visual scene data.

---

## What Spectra is trying to become

The long-term product is a scientific scene engine able to accept structured scientific intent and produce coherent static, animated, realtime, or cinematic visualizations.

Possible future inputs:

- formulas and equations;
- structured Python APIs;
- versioned Spectra scene documents;
- lesson/storyboard templates;
- simulation data;
- natural-language requests compiled by an AI layer.

Possible outputs:

- interactive scientific scenes;
- Blender scenes and cinematic renders;
- realtime WebGPU/desktop/mobile viewers;
- images/video;
- reusable lesson timelines;
- remote render jobs;
- scientific visualization embedded in other products.

The deterministic engine must remain useful without AI and without Blender.

---

# Why the original architecture was reset

The old prototype successfully proved that formulas, graphs, calculus helpers, labels, animation, and lesson-style scenes could be generated inside Blender.

It also revealed the main scalability failure: scientific semantics, numerical computation, Blender geometry, Blender materials, frame state, UI state, labels, and animation logic became coupled.

The old growth pattern was approximately:

```text
new topic
 -> new Blender operator
 -> new Blender objects
 -> new custom update/frame logic
 -> new UI state
 -> larger renderer-coupled feature module
```

That can produce many demos, but it does not produce a general scientific engine.

Physics makes the coupling much worse: fields, trajectories, ODE/PDE solutions, particles, waves, tensors, coordinate transforms, constraints, operators, and simulations would each create more renderer-specific scientific code.

The new growth pattern is:

```text
new topic
 -> semantic domain object/capability
 -> compose existing mathematical capabilities
 -> compile to generic visual primitives
 -> existing Scene/Timeline
 -> existing renderer backends
```

The target is that adding the 100th scientific concept remains controlled.

---

# Core rule

**Adding a new scientific subject is not, by itself, a reason to modify `spectra.core`.**

Core changes should happen only when several unrelated domains expose the same genuinely universal missing abstraction.

Examples:

- coordinate frames belong in core;
- transforms belong in core;
- animation tracks belong in core;
- generic scene primitives belong in core;
- Coulomb's law does **not** belong in core;
- a Gaussian distribution does **not** belong in core;
- quantum observables do **not** belong in core;
- graph shortest-path algorithms do **not** belong in core.

Scientific knowledge lives in domains.

---

# Current architecture

## 1. Core values and scientific space

Current foundation includes:

- `Vec2`, `Vec3`, `Color`;
- vector dot/cross/normalization operations;
- SI-style `Dimension`, `Unit`, and `Quantity` foundations;
- `CoordinateFrame3D` with validated linearly-independent bases and handedness;
- `Quaternion`;
- `Transform3D`;
- renderer-independent `Transform3D.look_at(...)`.

Scientific coordinates stay scientific data. Renderer backends are responsible for mapping Spectra coordinates into their native coordinate convention.

## 2. Renderer-independent primitives

Current generic primitives include:

- `Point`;
- `Polyline`;
- `Surface` (indexed triangle surface);
- `Region`;
- `VectorGlyph`;
- `TextLabel`;
- `Group`;
- `Camera`.

All primitives share:

- stable `id`;
- visibility;
- opacity;
- renderer-neutral `Transform3D`.

`Polyline` additionally exposes `trim_start` / `trim_end`, allowing draw/reveal animation without renderer-specific curve hacks.

`Camera` is also a Spectra primitive. Camera position/orientation/projection therefore do not belong to Blender. The camera convention is local `-Z` forward and local `+Y` up; a backend maps this into its native camera convention.

## 3. Scene

`Scene` currently owns:

- generic primitives;
- an engine-owned `Timeline`;
- a scientific `CoordinateFrame3D`;
- optional `active_camera_id`.

Scene validation currently checks, among other things:

- unique primitive IDs;
- valid group child references;
- no group hierarchy cycles;
- valid active-camera references;
- valid animation targets;
- valid animation property paths;
- animation value compatibility;
- primitive invariants before a backend sees the scene.

`Scene.sample(t)` evaluates animation into a **static renderer-neutral Scene snapshot**.

That is an important contract: Blender/WebGPU/etc. are not the source of animation truth.

## 4. Animation engine

Animation currently supports engine-owned:

- `Keyframe`;
- `Track`;
- `Timeline`;
- `step`, `linear`, and `smooth` interpolation;
- interpolation of numeric values, vectors, colors, tuples, and quaternions;
- quaternion slerp;
- immutable nested property-path updates;
- reusable `fade_track`, `draw_track`, and `move_track` helpers.

Generic presentation operations live outside scientific domains. For example `staggered_reveal(scene)` can animate a function plot, graph, probability visualization, or physics scene without those domains implementing their own renderer-specific reveal code.

## 5. Versioned Scene document

Spectra Scene serialization currently uses:

```text
schema: spectra.scene
version: 2
```

Scene JSON v2 serializes:

- primitives;
- surface topology;
- transforms;
- opacity/path trim state;
- camera parameters;
- active camera;
- coordinate frame;
- timeline tracks/keyframes/interpolation.

The reader currently retains compatibility with v1 defaults.

This document boundary is intended to support:

- saved projects;
- CLI tools;
- remote render services;
- other language implementations;
- AI-generated scene descriptions;
- Blender/WebGPU/backend handoff.

## 6. Domain registry and capability graph

Scientific modules plug into `DomainRegistry`.

Domains may publish:

- semantic types;
- computation capabilities;
- generic visualization compilers.

Domains consume other domains through stable capability contracts rather than copying their algorithms.

Current registry behavior includes:

- dependency declarations;
- required and optional capabilities;
- **minimum capability contract versions**;
- automatic dependency-order resolution with `add_domains(...)`;
- arbitrary input order;
- diagnostic unresolved dependencies;
- atomic single-domain registration;
- atomic batch registration/rollback;
- semantic-type-directed visualization dispatch with `registry.compile_scene(obj)`.

Example:

```text
linear_algebra.normalize_complex
probability.discrete_distribution
linear_algebra.complex_quadratic_form >= v2
        -> physics.quantum
```

A capability implementation can later move from pure Python to NumPy, SciPy, Rust, C++, or GPU compute while keeping the public contract stable.

---

# Current scientific domains

The present modules are intentionally small vertical slices. They prove composition; they are not claims of complete scientific coverage.

## Mathematics

Current mathematics foundations include:

- safe AST-based expressions;
- `Interval`;
- `RectDomain2D`;
- `Function1D`;
- `Function2D`;
- parametric 3D curves;
- parametric 3D surfaces;
- scalar/vector field foundations;
- regular 3D sampling grids.

Current visualization paths include:

```text
Function1D -> Polyline
Function2D -> Surface
ParametricCurve3D -> Polyline
ParametricSurface3D -> Surface
VectorField3D -> VectorGlyph Scene
```

## Calculus

Calculus is a domain, not core.

Current capabilities include:

- numerical derivative-at-point;
- tangent sampling;
- reference numerical integration (composite Simpson rule).

`calculus.integrate` is a versioned capability so later native/adaptive/GPU implementations can replace the current deterministic reference implementation.

## Probability

Discrete probability currently includes:

- outcomes;
- `DiscreteDistribution`;
- expectation;
- variance;
- distribution Scene compilation.

Continuous probability is a separate subdomain:

```text
mathematics.Function1D
        +
calculus.integrate >= v2
        -> probability.continuous
```

Current continuous capabilities include:

- non-normalized finite-domain density input;
- computed normalization;
- normalized PDF;
- CDF;
- probability over intervals;
- PDF Scene visualization.

## Statistics

Current statistics foundation includes dataset/summary/histogram-style semantics and reuses probability capabilities instead of creating a separate probability implementation.

## Linear algebra

Current foundations include:

- real vectors;
- complex vectors;
- inner products;
- norms/normalization;
- real matrices;
- complex matrices;
- matrix-vector products;
- transpose/conjugate transpose;
- Hermitian checks;
- complex quadratic forms;
- complex identity matrices.

Matrix/Hermitian capabilities are versioned contracts.

## Differential equations

Current differential-equations domain includes a deterministic RK4 reference solver for first-order systems.

The important architecture is not RK4 itself. The important part is that physics depends on an ODE solver capability instead of owning a solver implementation.

## Graph theory

Graph theory was intentionally added because it is structurally different from continuous calculus/physics.

Current foundation includes:

- graph/edge semantics;
- directed/undirected neighbors;
- unweighted shortest path;
- explicit 2D graph layout;
- graph Scene visualization.

The fact that this was added without making graph-specific changes to core is an architecture proof.

---

# Current physics composition proofs

## Mechanics

```text
ODE first-order system + RK4 capability
        -> ParticleProblem
        -> Trajectory
        -> static trajectory Scene
        -> animated trajectory Timeline
```

The animated trajectory uses physical trajectory times to drive a moving generic `Point` and path drawing in the Spectra timeline.

No Blender frame state is required.

## Electromagnetism

The current electromagnetic slice describes point charges / Coulomb electric fields while reusing mathematical `VectorField3D`.

```text
mathematics.VectorField3D
        -> electromagnetic law
        -> generic vector field
        -> VectorGlyph Scene
```

Gravity, magnetic fields, fluid velocity fields, and future custom fields can reuse the same visual path.

## Quantum

Quantum currently reuses both probability and linear algebra.

Current foundation includes:

- normalized quantum state amplitudes;
- measurement distribution;
- Hermitian `QuantumObservable` semantics;
- operator application;
- expectation values.

Example composition:

```text
ComplexVector
ComplexMatrix >= v2
Hermitian check >= v2
Quadratic form >= v2
DiscreteDistribution
        -> QuantumState / QuantumObservable
```

Quantum does not implement its own matrix normalization, matrix-vector product, Hermitian test, or probability distribution.

This is the intended domain-composition model.

---

# Renderer backend contract

A backend is deliberately small.

Current conceptual contract:

```text
Backend
  name
  capabilities
  create(static_scene) -> handle
  apply(handle, static_scene)
  destroy(handle)
```

`BackendSession` owns playback/seek behavior:

```text
source animated Scene
        -> Scene.sample(t)
        -> static Scene
        -> backend.apply(...)
```

A renderer therefore does not need calculus/physics/domain imports.

`MemoryBackend` is the current renderer-free reference implementation proving the adapter boundary.

Planned real backends include:

- Blender;
- realtime/WebGPU or another suitable realtime engine;
- potentially Unreal/Godot/other adapters where product needs justify them.

**"Any 3D engine can be connected" does not mean zero adapter code.** Each renderer needs a backend mapping Spectra primitives/transforms/camera into its native objects. The scientific engine and domain code should not be rewritten.

---

# Forbidden architectural directions

These rules are deliberate.

## 1. No renderer SDK inside semantic core

`spectra.core` must not import Blender `bpy`, Unreal, Three.js, WebGPU APIs, Qt, or another renderer/UI SDK.

## 2. Do not add a scientific concept as a renderer feature

Bad:

```text
IntegralFeature -> create Blender mesh/material/keyframes
```

Correct direction:

```text
integral semantics
 -> generic Region/Polyline/labels/timeline
 -> backend
```

## 3. No Blender frame state as scientific time

Time belongs to Spectra. A backend may map seconds to native frames, but backend frame state is not the model.

## 4. No giant subject tool files

Do not recreate `calculus_tools.py`, `physics_tools.py`, etc. containing scientific semantics + UI + geometry + animation + renderer state.

## 5. No scientific truth hidden in renderer object names

Scientific relationships must exist in typed domain data before rendering.

## 6. Do not make UI panels the data model

UI edits/creates semantic data or documents. Headless engine behavior must remain available.

## 7. Do not optimize for feature count

One universal abstraction that makes twenty concepts cheap is preferable to twenty bespoke demo buttons.

## 8. AI is a compiler/client, not core truth

Natural language may later compile into Spectra semantics. Deterministic validation and execution must work without AI.

## 9. Templates are compositions

"Derivative lesson", "electric-field lesson", or "quantum lesson" are compositions/templates, not primitive engine capabilities.

## 10. Do not add generated release ZIPs to source control

Use Releases/CI artifacts.

---

# Current repository shape

Representative structure:

```text
spectra/
  core/
    animation.py
    coordinates.py
    expressions.py
    primitives.py
    scene.py
    serialization.py
    transforms.py
    types.py
    units.py

  domains/
    registry.py
    mathematics/
    calculus/
    probability/
    statistics/
    linear_algebra/
    differential_equations/
    graph_theory/
    physics/

  backends/
    base.py
    driver.py
    memory.py

  compiler.py
  presentation.py
  visualization.py

docs/
  DOMAIN_SYSTEM.md

tests/
  ... semantic/domain/animation/serialization/backend tests ...
```

---

# Validation status

Many unit tests now exist for:

- domain registration/dependency resolution;
- atomic rollback;
- capability versions;
- expression safety/functions;
- calculus;
- discrete/continuous probability;
- statistics;
- linear algebra;
- quantum composition;
- ODE/mechanics;
- electromagnetism/fields;
- graph theory;
- visualization dispatch;
- parametric/surface visualization;
- Scene serialization;
- animation sampling;
- Camera/transform behavior;
- backend adapter behavior;
- generic presentation animation.

**Important:** during this development session, GitHub Actions jobs have been failing before executing workflow steps and do not provide usable test logs. Full local `pytest` execution has intentionally been postponed because the local agent/environment is occupied. Therefore do **not** claim the current branch is fully test-green until a local run is performed.

When local access is available, the first validation step is:

```bash
git checkout main
git pull
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

Fix all failures before treating the foundation as stable.

---

# Near-term roadmap

## A. Validate the current foundation locally

Run the complete test suite and fix any runtime/type/integration errors introduced during rapid architecture work.

## B. Stabilize Scene/backend contract

Before large renderer work, verify:

- transform conventions;
- camera conventions;
- grouping semantics;
- coordinate-frame mapping;
- animation sampling;
- Scene JSON v2 round-trip;
- backend compatibility checks.

## C. First real Blender backend vertical slice

Target:

```text
Function1D / Surface / VectorField / trajectory
        -> generic Scene
        -> Scene.sample(t)
        -> BlenderBackend
        -> Blender objects/camera
```

`bpy` must exist only in Blender backend/addon integration code.

Start small. Do not immediately port the old addon UI.

## D. Rebuild scientific visualizations as compositions

Examples:

- tangent/derivative visualization;
- integral region/accumulation;
- animated probability distribution;
- vector field;
- mechanics trajectory;
- simple quantum-state visualization.

## E. Add deeper domains only through composition

Candidates include:

- geometry;
- complex analysis;
- more statistics;
- dynamical systems;
- PDEs;
- waves;
- fluid dynamics;
- relativity;
- quantum dynamics;
- topology;
- tensors.

Do not add all of them for feature-count reasons. Add them when they expose useful reusable abstractions or product use-cases.

---

# Definition of a good new scientific feature

Before implementing it, answer:

1. What is the scientific semantic object/relationship?
2. Which existing domain capabilities can it reuse?
3. Does it really require a new capability?
4. Which generic Scene primitives express it?
5. Which Timeline tracks express its animation?
6. Can it run headlessly without Blender?
7. Can a second renderer consume the same Scene?
8. Does this change core for a genuinely universal reason, or only because the new subject is unfamiliar?

If implementation starts with "create this Blender object/operator/panel", it is probably at the wrong layer.

---

# Engineering rules

- Keep renderer dependencies behind backend boundaries.
- Prefer immutable core/domain value objects where practical.
- Keep scientific computation separate from presentation.
- Reuse capabilities across domains rather than copy algorithms.
- Version capability contracts when semantics/API materially evolve.
- Keep domain loading atomic.
- Keep deterministic inputs deterministic.
- Explicitly document coordinate/time/unit conventions.
- Keep scene/document formats versioned.
- Avoid premature dependency lock-in to SymPy/NumPy/SciPy; adopt them when the capability requirements justify them.
- Heavy computation may later move behind stable contracts to NumPy, Rust, C++, SIMD, GPU compute, or remote services.
- Tests should prove composition, not only individual algorithms.

---

# Branch policy

- `main`: new renderer-independent architecture.
- `legacy/pre-semantic-core-2026-08-30`: complete pre-reset Blender-addon snapshot.
- Generated builds/renders/ZIPs do not belong on `main`.

The architectural-reset work in this session has intentionally been applied directly to `main` with repository-owner approval. Future stabilization/release work may use focused branches/PRs as appropriate.

---

# Continuation instructions for another ChatGPT/Codex session

If the previous chat is unavailable or reaches its context limit:

1. Read this README completely.
2. Read `docs/DOMAIN_SYSTEM.md`.
3. Inspect latest `main`.
4. Do **not** resume development from the legacy calculus addon.
5. Do **not** put `bpy` into `spectra.core` or scientific domains.
6. Preserve versioned capability composition.
7. Preserve atomic domain registration.
8. Preserve `semantic object -> generic Scene -> Scene.sample(t) -> backend` separation.
9. Reuse existing mathematics/probability/linear-algebra/ODE/field semantics before inventing physics-specific duplicates.
10. Keep Camera and animation engine-owned, not Blender-owned.
11. Keep Scene JSON versioned/backward-conscious.
12. Run local tests as soon as the local environment becomes available; current GitHub Actions status is not sufficient validation.
13. Update this README whenever a fundamental contract changes.

The next major engineering milestone is **local validation followed by the first minimal Blender backend**, not a return to rapid one-off scientific feature buttons.

---

# Success criterion

Spectra is architecturally succeeding when a new scientific idea usually requires:

```text
new semantics and/or composition of existing capabilities
        -> existing generic visual primitives
        -> existing timeline
        -> existing renderer backends
```

—not a new renderer-specific subsystem.

The desired end state is a **scientific engine with Blender support**, not a Blender addon that accumulated scientific features.
