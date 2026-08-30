# Spectra Science

Spectra Science is a **renderer-independent scientific visualization engine** under active pre-alpha development.

The complete original Blender-addon prototype is preserved on:

```text
legacy/pre-semantic-core-2026-08-30
```

`main` is the new semantic-engine architecture. Do not rebuild new work on the legacy addon design.

Read these documents before extending the engine:

- `docs/DOMAIN_SYSTEM.md`
- `docs/DOMAIN_CATALOG.md`
- `docs/BLENDER_BACKEND.md`
- `docs/GEOMETRY_RELATIVITY_PDE.md`

## Product thesis

Spectra is not a collection of Blender science buttons. Scientific meaning exists before renderer objects.

```text
scientific intent
    -> domain semantics
    -> reusable computation capabilities
    -> visualization compiler
    -> generic Scene + Timeline
    -> Scene.sample(t)
    -> renderer backend
```

Possible authoring surfaces include formulas, Python APIs, declarative documents, simulation/data inputs, lesson templates, and later AI compilation. Possible outputs include Blender, realtime clients, saved Scene documents, images/video, interactive lessons, and remote/headless rendering.

The engine must remain useful if Blender disappears tomorrow.

## Core rule

**Core is not calculus, quantum physics, relativity, or Blender.**

Core owns only reusable cross-domain/cross-renderer abstractions:

- vectors/colors/transforms/coordinates/bounds;
- units, quantities, dimensions, typed physical constants;
- restricted expression infrastructure;
- generic Scene primitives/resources;
- Timeline/interpolation;
- Scene composition and namespacing;
- Scene serialization;
- domain/backend contracts.

A new scientific subject is not sufficient reason to modify Core.

## Domain architecture

`DomainRegistry` is runtime authority. `DomainCatalog` discovers providers and computes dependency closure. Domains consume stable versioned capability names rather than importing each other's private algorithms.

Current bundled domain graph includes:

```text
mathematics
calculus
linear_algebra
tensor_algebra
differential_geometry
└── differential_geometry.geodesics
probability
└── probability.continuous
statistics
graph_theory
differential_equations
partial_differential_equations
├── partial_differential_equations.2d
└── partial_differential_equations.complex
physics
├── mechanics
├── particles
├── diffusion
│   └── diffusion.2d
├── waves
├── electromagnetism
├── quantum
│   ├── quantum.spatial
│   └── quantum.schrodinger1d
└── relativity
    └── relativity.general
```

Examples of composition already present:

```text
linear algebra + probability
    -> finite-dimensional quantum

ComplexFunction1D + calculus + continuous probability
    -> spatial quantum wavefunction

ODE RK4
    -> real PDE
    -> diffusion

ODE RK4
    -> complex PDE
    -> Schrodinger evolution

Tensor algebra + linear algebra inverse
    -> differential geometry curvature
    -> general relativity adapter

Christoffel symbols + ODE RK4
    -> geodesics

2D PDE Laplacian + ODE RK4
    -> 2D diffusion
```

## Mathematics and geometry foundation

Current semantics/capabilities include:

- `Interval`, rectangular domains;
- expression-backed and callable real functions;
- complex-valued functions;
- 2D functions;
- parametric curves/surfaces;
- scalar/vector/time-dependent fields;
- calculus derivative/integration/gradient/divergence/curl;
- real/complex vectors and matrices;
- determinant/inverse and Hermitian/operator tools;
- arbitrary-rank dense tensors, contraction, trace, outer products;
- metric tensor fields;
- index raising/lowering;
- Christoffel symbols;
- Riemann, Ricci, and scalar curvature;
- geodesic ODE semantics and explicit 3D projection views.

Metrics may be positive-definite or indefinite. Renderer code must never guess how higher-dimensional coordinates should be projected.

## PDE foundation

Time integration is reused through the generic ODE capability instead of duplicated per PDE/physics domain.

Current PDE layers include:

- uniform 1D grids;
- uniform 2D rectangular grids;
- fixed / periodic / zero-gradient boundary modes;
- 1D second derivative;
- 2D five-point Laplacian;
- real method-of-lines evolution;
- complex-state method-of-lines adapter;
- animated 1D profiles;
- animated topology-stable 2D `Surface` geometry.

A 2D PDE animation changes only `Surface.vertices`, allowing incremental backends to update native buffers without rebuilding topology.

## Physics foundation

Current architecture proofs/foundations include:

- Newtonian mechanics;
- multi-particle systems;
- 1D and 2D diffusion;
- harmonic waves and superposition;
- Coulomb fields and plane EM waves;
- finite-dimensional quantum states/observables;
- normalized spatial wavefunctions;
- 1D time-dependent Schrodinger evolution;
- special relativity events/intervals/proper time/four-velocity;
- Schwarzschild metric semantics;
- Einstein tensor built from generic curvature capabilities.

These are foundations, not claims that each scientific subject is complete.

## Units and constants

`Dimension`, `Unit`, and `Quantity` support dimensional conversion and arithmetic.

Typed constants currently include:

- speed of light;
- elementary charge;
- Planck constant;
- reduced Planck constant;
- Boltzmann constant;
- Coulomb constant;
- gravitational constant.

Physics may cache SI floats in hot loops, but typed quantities remain the source of dimensional meaning.

## Generic Scene vocabulary

Current reusable primitives include:

- `Point`, `PointCloud`;
- `Polyline`;
- `Surface`, `Region`;
- `VectorGlyph`, `VectorGlyphSet`;
- `TextLabel`, `Group`;
- `Camera`, `Light`.

A Scene also owns materials, coordinate frame, active camera, and Timeline.

Dense scientific data must remain batched. Many particles should normally be one `PointCloud`; large vector fields should normally be one `VectorGlyphSet`.

## Animation and composition

Spectra owns scientific time:

```text
Scene + Timeline
    -> Scene.sample(t)
    -> static Scene snapshot
    -> backend.apply(snapshot)
```

Backends must not become the source of scientific timing.

Animation supports numeric/vector/color/quaternion/tuple interpolation, transforms, opacity, path reveal, particle arrays, dynamic polyline points, surface vertices, vector-field arrays, and cameras.

`spectra.core.composition` namespaces and composes independent domain Scenes without requiring local IDs to be coordinated in advance.

## Scene documents

Current Scene schema is:

```text
spectra.scene v4
```

Readers retain compatibility with versions 1-3. Schema changes must be deliberate and backward compatibility must not be silently broken.

## Backends

### MemoryBackend

Renderer-free reference backend.

### BlenderBackend

Reference Blender adapter with lazy `bpy`/`mathutils` imports. Blender SDKs must never enter Core or scientific domains.

### IncrementalBlenderBackend

Performance-oriented adapter preserving stable Spectra IDs as stable Blender objects and updating common data buffers in place where possible.

Dense mapping rule:

```text
PointCloud     -> one Blender mesh object
VectorGlyphSet -> one Blender Curve object with many splines
```

Current fast paths include point/particle positions, polyline points, surface vertices, vector-field arrays, and transform/visibility-only changes.

`BlenderTimelineController` maps Blender transport frames to Spectra engine time; Blender controls playback transport, Spectra owns the timeline semantics.

Native Blender execution is still pending because Blender was not installed in the current local validation environment.

## Testing status

Last validated local baseline **before the current geometry/relativity/2D-PDE batch**:

```text
pytest:             124 passed
compileall spectra: PASS
import boundary:    PASS
DomainCatalog:      PASS
serialization v1-4: PASS
dense batching:     PASS
```

Measured plain-Python batch/update reference results from that validation included roughly:

```text
10k batched updates: ~9.6-9.8 ms
1024-point wave:     ~0.82 ms
```

Those numbers are not Blender rendering benchmarks.

The current batch adds curvature, geodesics, relativity/GR, 2D PDE, and 2D diffusion code plus new tests. **Do not claim a new green baseline until the full local suite is run again.**

GitHub Actions is intentionally absent by user request. Do not recreate it unless explicitly requested.

## Forbidden regressions

Do not:

- import renderer SDKs into Core/domains/generic compilers;
- implement new science directly as Blender operators/objects;
- recreate giant subject-specific tools modules;
- make UI state the scientific model;
- make AI the deterministic engine core;
- duplicate math/solver algorithms inside physics when capabilities already exist;
- expand dense data into thousands of Scene/backend objects;
- let a backend invent missing scientific semantics;
- store generated release ZIPs/build artifacts in source control.

## Repository policy

- `main` — current semantic engine.
- `legacy/pre-semantic-core-2026-08-30` — preserved old addon.
- generated caches/renders/builds/releases do not belong in source control.

## Next validation milestone

After pulling current `main`, run the complete test suite plus the targeted cases in `docs/GEOMETRY_RELATIVITY_PDE.md`.

If that batch passes, the next larger development phase can continue from a new verified baseline. Native Blender smoke/performance validation remains a separate milestone.

## Success criterion

A new scientific idea should usually require:

- new semantics or composition of existing semantics;
- reuse of existing computation capabilities;
- compilation into existing generic visual primitives;
- tests;

and **not** require another renderer-specific subsystem.

Spectra should become a scientific scene engine with Blender support, not a Blender addon that accumulated scientific features.
