# Spectra Science

Spectra Science is being rebuilt as a **renderer-independent scientific visualization engine** for mathematics and physics.

This repository is not intended to become a collection of one-off Blender buttons for derivatives, integrals, limits, vector fields, waves, and every future scientific topic. The long-term goal is a small semantic engine capable of expressing many scientific concepts through reusable primitives, timelines, relationships, and renderer backends.

> Project status: architectural reset / pre-alpha. The previous Blender-addon implementation is preserved on the branch `legacy/pre-semantic-core-2026-08-30`.

## Why the reset exists

The original prototype proved that useful scientific scenes can be generated inside Blender. It could parse formulas, build graphs, create derivative/integral/limit helpers, animate parameters, and assemble lesson-style scenes.

That prototype also exposed the central architectural problem: scientific meaning, numerical evaluation, animation state, Blender objects, materials, collections, HUD text, and UI settings became coupled together. A calculus feature could directly import `bpy`, create curves and meshes, inspect Blender frame state, evaluate formulas, and update presentation objects in the same module.

That approach is acceptable for a prototype. It is not a scalable foundation for a general math/physics visualizer.

If we continued the old direction, progress would look like this:

`new scientific topic -> new Blender operator -> new Blender objects -> new custom animation code -> more UI state`

The codebase would grow feature-by-feature while the engine itself would not become meaningfully more general. Physics would make this worse: vector fields, particle systems, trajectories, differential equations, waves, coordinate transforms, constraints, scalar fields, tensors, and simulations would each introduce more domain logic directly into renderer code.

The reset changes the direction to:

`scientific intent -> semantic model -> visual primitives -> animation graph -> renderer backend`

Blender is therefore a backend, not the scientific model.

---

## Product thesis

The product is not "a Blender graph addon".

The product should eventually allow a user, script, lesson template, or AI system to describe a scientific idea and obtain a coherent visual scene without manually authoring renderer-specific geometry.

Examples of future inputs may include:

- a formula or equation;
- a structured Python API;
- a declarative scene document;
- a lesson/storyboard template;
- a natural-language request compiled by an AI layer.

Examples of outputs may include:

- interactive scientific scenes;
- Blender scenes for high-quality rendering;
- realtime WebGPU/desktop/mobile visualization;
- images or video;
- reusable lesson timelines.

The core must remain useful even if Blender disappears from the project tomorrow.

---

## Non-goals and forbidden architectural directions

These rules are intentionally explicit so a future contributor or a new ChatGPT session does not accidentally rebuild the old architecture.

### 1. Do not add scientific concepts as renderer-specific features

Bad:

`IntegralFeature` directly creates a Blender mesh and material.

Better:

An integral is represented semantically using a function/domain/accumulation description. A compiler lowers that meaning into generic primitives such as curves, regions, markers, labels, and timeline tracks. A backend decides how those primitives become actual geometry.

### 2. No `bpy` inside the semantic core

The packages under `spectra.core` must not import Blender, Three.js, WebGPU, Qt, Unreal, Manim, or any other renderer/UI framework.

Renderer dependencies live under adapters/backends only.

### 3. Do not make Blender frame state the source of scientific truth

Time is an engine value. A backend may map engine time to Blender frames, but the semantic model and animation graph must be evaluable independently.

### 4. Do not store scientific meaning only as object names/tags

Renderer object metadata is an implementation detail. Scientific relationships must exist in typed engine data before rendering.

### 5. Do not build one giant `calculus_tools.py`, `physics_tools.py`, or equivalent

A domain module may contain compilers and domain semantics, but generic presentation behavior belongs in reusable primitives and systems.

### 6. Do not confuse templates with core capabilities

"Derivative lesson", "FTC lesson", or "electric-field lesson" are templates/compositions. They are not fundamental engine primitives.

### 7. Do not optimize for feature count

A release is not successful because it adds ten new math buttons. Prefer one reusable abstraction that makes ten future concepts cheap.

### 8. Do not make natural language or AI the core

AI can compile user intent into the semantic model later. The deterministic semantic model, validation, scene compiler, and renderer contracts must work without AI.

### 9. Do not let UI property panels become the data model

UI reads/writes commands or documents. The engine model must be serializable, testable, and usable headlessly.

### 10. Do not commit generated release ZIPs to `main`

Release artifacts belong in GitHub Releases / CI artifacts, not version-controlled source trees.

---

## Architecture

### Layer 1 — Scientific/domain semantics

This layer describes **what exists scientifically**, not how it is rendered.

Likely domain entities include:

- scalar functions and sampled functions;
- equations and expressions;
- domains and coordinate systems;
- parametric curves and surfaces;
- scalar fields and vector fields;
- trajectories;
- particle systems;
- waves;
- measurements and annotations;
- calculus concepts such as tangent/derivative/accumulation;
- later: differential-equation solutions, tensors, constraints, simulation state.

Not every item above needs its own permanent class. We should add domain abstractions only when they capture reusable meaning.

### Layer 2 — Visual primitives

This is the renderer-independent visual vocabulary.

Initial primitives include concepts such as:

- `Point`
- `Polyline`
- `Surface`
- `Region`
- `VectorGlyph`
- `TextLabel`
- `Group`

Later candidates may include instanced glyph sets, volumes, trails, particles, axes/grids, and camera/light descriptions.

A physics concept should preferably compile into the same primitives used by mathematics rather than introducing a new rendering path for each topic.

### Layer 3 — Animation graph

Animation is data, not imperative Blender frame-handler code.

A timeline describes tracks that map time to properties. Initial interpolation can be simple; the important part is ownership and separation.

Examples:

- animate a point's position;
- reveal a curve;
- change a domain bound;
- animate vector magnitudes;
- move a camera;
- change opacity or emphasis.

Backends translate engine time/tracks to their native animation systems when useful.

### Layer 4 — Scene compiler

The compiler lowers scientific/domain descriptions into a `Scene` containing renderer-independent primitives and animations.

This boundary is where reusable scientific visualization logic belongs.

Examples:

- a function over a domain -> sampled polyline;
- a tangent visualization -> function polyline + point + tangent line + labels;
- an integral visualization -> function polyline + signed region + bounds/labels;
- a vector field -> field sampler + vector glyph instances;
- a trajectory -> polyline/trail + moving marker.

### Layer 5 — Renderer backends

A backend consumes the generic `Scene` contract.

Planned backends may include:

- Blender — cinematic/high-quality authoring and rendering;
- realtime backend (WebGPU or another suitable engine) — interactive applications;
- debug/reference backend — tests and deterministic inspection.

A backend may offer capabilities not present in every renderer, but it must not leak renderer-specific state into the semantic core.

### Layer 6 — Products/interfaces

On top of the engine we can build:

- Blender addon UI;
- desktop/web/mobile application;
- lesson/template library;
- Python SDK;
- CLI/render service;
- AI scientific-scene authoring.

These are consumers of the engine, not the engine itself.

---

## Current source layout

```text
spectra/
  core/
    primitives.py   # renderer-independent visual vocabulary
    scene.py        # scene graph/document
    animation.py    # engine-owned timeline/tracks
    types.py        # basic immutable math/value types
  backends/
    base.py         # backend protocol
  compiler.py       # first generic compilation utilities

tests/
  test_semantic_core.py
```

This is deliberately small. We should earn complexity rather than pre-building a huge framework.

---

## Core invariants

The following invariants should be protected by tests and code review:

1. `spectra.core` imports no renderer SDK.
2. A `Scene` can be created and inspected in plain Python.
3. Core scene data is serializable or has a clear path to serialization.
4. Scientific coordinates are distinct from backend/world coordinates.
5. Time is represented independently of Blender frames.
6. IDs and relationships are stable and explicit.
7. A backend can be replaced without rewriting scientific-domain algorithms.
8. Compilers should be deterministic for deterministic inputs.
9. One semantic concept should reuse existing primitives whenever possible.
10. Renderer-specific optimizations must remain behind backend boundaries.

---

## What was wrong with the previous prototype

The old code is preserved for reference, not shame. It successfully validated ideas, but it should not be copied forward blindly.

Observed problems:

- Formula evaluation and Blender context/settings were coupled.
- Scientific coordinates and Blender world coordinates were coupled through helper functions.
- Calculus logic directly created Blender curves, meshes, materials, text objects, and collections.
- Animation read Blender's current frame directly rather than evaluating an engine timeline.
- Scientific relationships were partially represented through Blender object names/custom properties.
- UI settings acted as both presentation controls and domain state.
- Derivative, integral, limit, HUD, geometry, timeline, and scene-maintenance responsibilities accumulated in a very large calculus module.
- Templates generated full renderer-specific lesson scenes instead of compiling declarative scientific intent.
- The repository stored many generated addon ZIP versions directly in source control.
- Version number growth gave the appearance of product maturity while architectural reuse remained limited.

Useful parts of the prototype should be ported selectively. For example, the formula parser's AST whitelist and safe-symbol approach are valuable ideas, but they should evolve into an engine-owned expression layer rather than depend on Blender settings.

---

## Migration strategy

Do **not** port every old feature immediately.

### Phase 0 — Preserve and reset (current)

- Freeze the old implementation on the legacy branch.
- Remove generated ZIPs and old tightly-coupled addon code from `main`.
- Establish core types, primitives, scene, timeline, backend protocol, and tests.

### Phase 1 — Prove the architecture with one vertical slice

Implement only enough to prove separation:

`function expression -> sampled scientific data -> generic Polyline Scene -> backend output`

Then add a Blender backend that renders that scene without putting `bpy` anywhere in core/compiler/domain code.

Acceptance criterion: the same scene can be inspected/tested without Blender and rendered through Blender via an adapter.

### Phase 2 — Calculus as compositions

Rebuild only a few concepts:

- moving point;
- secant/tangent;
- derivative visualization;
- signed integral region.

Each must compile into generic primitives and timeline tracks. If rebuilding a calculus lesson requires a new Blender-specific scientific implementation, architecture has regressed.

### Phase 3 — Physics proof

Add a vector field and trajectory/wave example. This phase is important because it proves the architecture is not secretly calculus-specific.

### Phase 4 — Authoring/document format

Define a stable scene/document representation and serialization strategy. Build CLI/Python SDK before making a large UI.

### Phase 5 — Product surfaces

Reintroduce Blender UI and/or create a realtime application. AI authoring can be layered on once deterministic contracts are stable.

---

## Definition of a good new feature

Before implementing a feature, answer:

1. What is the scientific meaning?
2. Is that meaning already expressible using existing domain objects?
3. Which generic visual primitives should represent it?
4. Which animation tracks are needed?
5. Does this require a core change, or only a compiler/template?
6. Can it run in a headless test without Blender?
7. Can another backend render the same result?

If the feature starts with "create this Blender mesh/operator/panel", it is probably being implemented at the wrong layer.

---

## Engineering rules

- Python code should be typed where it materially clarifies contracts.
- Prefer immutable value objects in core.
- Keep dependencies minimal in the semantic core.
- Add unit tests for semantic behavior before backend polish.
- Avoid hidden global state.
- Keep numeric algorithms separate from presentation when practical.
- Explicitly document coordinate conventions and units.
- Avoid premature symbolic-math dependency lock-in; add libraries such as SymPy only when requirements justify them.
- Performance-sensitive sampling/simulation may later move to NumPy/Rust/C++/GPU implementations behind stable contracts.
- Public APIs should evolve deliberately; pre-alpha internals may change aggressively.

---

## Repository/branch policy

- `main`: new architecture only.
- `legacy/pre-semantic-core-2026-08-30`: complete snapshot of the previous Blender-addon prototype before the reset.
- Experimental work should normally happen on focused branches and merge through reviewable commits/PRs.
- Generated ZIPs, renders, caches, and build artifacts should not be committed to `main`.

---

## Continuation instructions for another ChatGPT/Codex session

If this conversation is unavailable or reaches its limit, start by reading this README and inspecting the latest `main` branch.

**Do not restart feature development from the old calculus addon.** The old implementation is reference material on `legacy/pre-semantic-core-2026-08-30`.

Continue in this order unless newer commits intentionally amend the roadmap:

1. Run/read the semantic-core tests.
2. Keep `spectra.core` renderer-independent.
3. Finish the first function-to-Polyline vertical slice.
4. Add a Blender backend adapter that consumes a generic `Scene`.
5. Prove the same scene is testable without Blender.
6. Port tangent/integral behavior as compiler compositions, not direct `bpy` feature modules.
7. Add a vector-field physics slice before building a large UI.
8. Update this README whenever an architectural decision changes.

When uncertain, optimize for **generality, separation, testability, and the cost of adding the 100th scientific concept**, not the speed of adding the next demo button.

---

## Success criterion

Spectra Science succeeds architecturally when a new scientific idea usually requires describing new semantics or composing existing primitives — **not creating an entirely new renderer-specific subsystem**.

The end state should feel like a scientific scene engine with Blender support, not a Blender addon that accumulated scientific features.
