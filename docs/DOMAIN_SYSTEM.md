# Spectra Science — Domain System

This document records the modular scientific-domain architecture used by Spectra Science.

Read it together with the repository `README.md`, `DOMAIN_CATALOG.md`, and `MODULE_SDK.md` before extending the engine.

## Core rule

Spectra Core must remain small, renderer-independent, and subject-neutral.

Core owns abstractions that remain useful across unrelated scientific domains, such as:

- numeric/vector/color types;
- transforms and coordinate frames;
- units, quantities, dimensions, typed constants;
- expression infrastructure;
- generic Scene primitives/resources;
- Timeline/interpolation;
- Scene composition/serialization;
- domain/backend contracts.

Core must not become a giant implementation of:

```text
calculus
probability
CFD
quantum mechanics
chemistry
Maxwell equations
relativity
Blender
CUDA
WebGPU
```

Scientific knowledge lives in independently registered domains.

## Current engine shape

```text
Spectra Core
    ↓
DomainCatalog
    ↓ discover/provider planning
DomainRegistry
    ├─ semantic types
    ├─ versioned capabilities
    ├─ numerical solver roles/implementations
    └─ visualization registry
            ↓
scientific solutions / fields / trajectories
            ↓
semantic visualization
            ↓
generic Scene + Timeline
            ↓
presentation policy
            ↓
renderer backend
```

Blender is one backend. A scientific module must remain meaningful without Blender installed.

## Capabilities, not implementation coupling

A domain publishes stable capabilities under names such as:

```text
mathematics.vector_field3d
pde.laplacian_3d
pde.solve_method_of_lines_3d
physics.mechanics.solve_particle
physics.potential_field3d
experiments.run_sweep
```

Another domain declares `DomainDependency` on the capability it needs.

It should not:

- copy the algorithm;
- depend on another domain's private file layout;
- import a renderer SDK;
- hardcode one numerical implementation when a stable role exists.

The capability contract is the dependency boundary.

The implementation behind it may move from Python reference code to native CPU/GPU/external execution without requiring dependent scientific domains to be rewritten.

## Domain discovery and catalog

Built-in domains are no longer maintained through one giant hand-edited provider manifest.

The current model is:

```text
strict ...Domain class discovery
    ↓
instantiate/probe-register domains
    ↓
observe actual registry.provide(...) ownership
    ↓
generate DomainDescriptor provider metadata
    ↓
compute dependency closure when loading
```

This prevents capability metadata from drifting away from runtime registration.

A semantic type that downstream domains depend on must be published with `registry.provide(...)`; merely calling `register_semantic_type(...)` is not enough for capability-based dependency resolution.

See `DOMAIN_CATALOG.md`.

## Runtime registration

`DomainRegistry` is the runtime authority.

It owns:

- loaded domain instances;
- semantic type registrations;
- capabilities and versions;
- capability provider ownership;
- visualization compilers;
- numerical solver implementations/policies.

Domain registration is transactional. If registration fails, partial registry/solver/visualization mutations must roll back.

This allows large dependency closures to fail safely rather than leaving a half-registered scientific environment.

## Automatic dependency resolution

Domains may be supplied in arbitrary order. Registration resolves declared required capabilities rather than depending on manual initialization sequence.

Bad architecture:

```text
always import math first
then PDE
then physics
then chemistry
```

Desired architecture:

```text
requested domain/capability
    ↓
provider closure
    ↓
dependency-resolved atomic registration
```

Missing providers/version incompatibilities must produce clear errors rather than silent scientific degradation.

## Scientific composition rule

Before implementing a new algorithm inside a higher-level domain, prefer existing lower-level capabilities.

Examples in the current architecture include:

```text
linear algebra + probability
    -> finite-dimensional quantum

complex fields + integration
    -> spatial quantum semantics

stable ODE role
    -> method-of-lines PDE
    -> diffusion / waves / Schrödinger / heat / chemistry / Maxwell

Poisson + gradient
    -> electrostatic potential
    -> gravitational potential

Poisson + divergence/gradient/advection
    -> incompressible-flow pressure projection

elasticity + vector second-order PDE
    -> elastodynamics

heat conduction + elasticity
    -> thermoelasticity

Maxwell fields + mechanics Lorentz force
    -> charged-particle trajectories

ReactionNetwork + coupled PDE
    -> reaction-diffusion

reaction enthalpy
    -> thermal source

J dot E
    -> electrothermal heating
```

The point is not only code reuse. Shared capabilities create one scientific contract that can later receive a faster implementation once.

## Numerical execution roles

Scientific domains should generally depend on **what numerical job must be done**, not one concrete algorithm name.

For first-order time integration:

```text
ode.first_order
```

is the stable role.

High-level domains use role-dispatched capabilities such as:

```text
ode.solve_first_order
```

The runtime may then choose among loaded implementations such as:

```text
rk4.reference
heun.reference
rk45.reference
future native_cpu/gpu/external providers
```

Selection may depend on execution/precision/order/adaptive requirements, problem compatibility, priority, or ordered policies.

The legacy/direct `ode.solve_rk4` capability remains useful for reference testing/compatibility but should not be the dependency that every high-level domain hardcodes.

See `SOLVERS_AND_EXPERIMENTS.md`.

## Semantic types

Scientific meaning should exist before visualization.

Examples:

```text
PotentialField3D
ParticleProblem
ChemicalReaction
ReactionNetwork
ScalarPDEProblem3D
MetricTensorField
ExperimentResult
```

Semantic objects should not store:

- Blender objects;
- GPU pointers/handles;
- UI widgets;
- renderer material node names;
- hidden render-unit conversions.

Unit/coordinate/boundary meaning should be explicit when scientifically relevant.

## Semantic visualization dispatch

Callers should not need an ever-growing switch statement such as:

```text
if quantum ...
elif CFD ...
elif chemistry ...
```

to compile a semantic object into a scene.

Domains register type-directed default visualization compilers through `VisualizationRegistry` when a sensible canonical view exists.

Examples:

```text
Function1D -> Polyline
Function2D -> Surface
Trajectory -> Polyline + Point
experiment response -> Polyline / PointCloud / labels
```

## Explicit view semantics

Not every scientific object has one canonical visualization.

For example:

```text
VectorField3D
    -> arrows
    -> integral curves
    -> slices

complex wavefunction
    -> real
    -> imaginary
    -> magnitude
    -> probability density
    -> phase
```

Such choices should be represented through explicit view semantics/policies rather than letting a renderer guess.

A renderer must never invent the scientific interpretation of a field.

## Generic Scene vocabulary

Current generic primitives include:

- `Point`;
- `PointCloud`;
- `Polyline`;
- `Surface`;
- `Region`;
- `VectorGlyph`;
- `VectorGlyphSet`;
- `TextLabel`;
- `Group`;
- `Camera`;
- `Light`.

Dense data must remain batched.

Examples:

```text
10,000 particles -> one PointCloud
large vector sample -> one VectorGlyphSet
```

Do not expand data into thousands of Scene/backend objects merely because a renderer can create them.

## Presentation layer

Scientific visualization and premium presentation are separate concerns.

The current engine already contains renderer-neutral presentation helpers such as timeline composition/staggered reveal.

The intended fuller layer is:

```text
semantic visualization
    -> scientifically correct base Scene
    -> PresentationIntent / preset / camera / colors / legends / annotations
    -> presentation-enriched Scene
    -> Blender/WebGPU/other backend
```

A physics domain may know that quantum phase is cyclic or temperature has units. It must not know which Blender shader or compositor node implements the chosen appearance.

See:

- `PREMIUM_PRESENTATION_SYSTEM.md`
- `BLENDER_PREMIUM_PRESENTATION.md`

## Scientific time vs presentation time

Spectra owns scientific time through `Scene + Timeline -> Scene.sample(t)`.

Presentation may compose reveal/camera/annotation animation around scientific evolution, but it must not silently alter physical time semantics.

Backends may use native playback transport, but renderer frame handlers must not become the source of scientific state.

## Units and coordinates

Physical domains must not hide units in renderer coordinates.

`Unit` / `Quantity` and coordinate-frame semantics exist independently from Blender/WebGPU world units.

Hot numerical code may convert values into SI floats for computation, but unit conversion should occur explicitly at the scientific/numerical boundary.

A backend maps already-defined scientific coordinates into its native representation.

## Scene transport

The generic `Scene` is both an in-process object and a renderer-independent transport model.

The versioned `spectra.scene` document allows the compiled scene to be consumed by:

- Blender;
- realtime/WebGPU clients;
- CLI/headless workers;
- remote rendering;
- saved projects/lessons;
- inspection/tests.

Do not serialize native Blender/Unreal/WebGPU objects into the scientific Scene document.

## Experiment domains

Experiments are first-class modules rather than UI-only scripts.

The current post-baseline architecture contains generic concepts for:

- parameter sweeps;
- batched case evaluation;
- solver comparison;
- convergence;
- sensitivity;
- deterministic uncertainty propagation;
- calibration;
- ranking/Pareto analysis;
- tracked numerical execution;
- durable experiment artifacts;
- renderer-neutral experiment views.

This means a future UI can orchestrate experiments without becoming the owner of scientific logic.

## External module/plugin direction

Built-in domains are auto-discovered from the Spectra package.

Third-party packages should eventually extend the catalog through explicit package metadata/entry points rather than editing Core or performing import-time global registration.

See:

- `MODULE_SDK.md`
- `PLUGIN_PACKAGING.md`

A plugin package may provide multiple domains, numerical implementations, views, or presentation resources.

## Where new subjects belong

Examples:

```text
calculus -> scientific domain
probability -> scientific domain
statistics -> scientific domain
linear algebra -> scientific domain
control systems -> scientific domain
optics -> scientific/physics domain
biology -> domain(s)
CFD -> physics domains consuming PDE/field capabilities
quantum -> physics domains consuming complex/linear-algebra/probability/PDE capabilities
new renderer -> backend package
new GPU solver -> numerical provider domain/plugin
premium theme -> presentation extension
```

## Rule for changing Core

Adding a new subject is not sufficient reason to modify Core.

Core should change only when several unrelated domains demonstrate the same missing universal abstraction.

Useful test:

> If this scientific subject disappeared tomorrow, would the abstraction still make sense for several unrelated domains?

If no, keep it in the domain.

Examples:

- units belong in Core;
- coordinate frames belong in Core;
- Coulomb's law does not;
- Navier–Stokes does not;
- a Blender Geometry Nodes rig does not.

## Renderer rule

Domain semantics do not create native renderer objects.

The pipeline is:

```text
scientific semantics
    -> generic Scene
    -> optional generic presentation enrichment
    -> backend
```

Blender backend code may be sophisticated. Physics code should remain unaware of it.

## Numerical backend rule

Likewise, scientific domains should not import device/runtime technology.

Bad:

```text
physics.maxwell imports CUDA
chemistry checks GPU brand
PDE decides to allocate Blender buffers
```

Desired:

```text
scientific domain -> stable solver role
solver registry -> selected native/GPU provider
```

See `NATIVE_NUMERICAL_BACKENDS.md`.

## Long-term scalability target

The target is not merely a long feature list.

The target is that the cost of adding the 100th, 500th, or organization-specific scientific module remains controlled.

A normal new module should mostly contain:

1. scientific semantic types;
2. declared capability dependencies;
3. subject-specific computation/relationships;
4. optional compositions into existing numerical roles;
5. generic visualization/view semantics;
6. tests and limitations.

It should not require rewriting:

- Core;
- DomainCatalog initialization order;
- renderer backend;
- animation system;
- units;
- Scene transport;
- all previous domains.

## Continuation checklist

When another developer/agent continues development:

1. Read root `README.md` and `docs/README.md`.
2. Keep Core free of subject-specific and renderer/device-specific knowledge.
3. Prefer capabilities over cross-domain private imports.
4. Publish every dependency-visible semantic contract with `provide()`.
5. Use role-dispatched numerical execution rather than hardcoding one solver in high-level domains.
6. Reuse existing fields/PDE/tensor/linear-algebra/mechanics capabilities before creating duplicates.
7. Use explicit view semantics when multiple visual interpretations are scientifically valid.
8. Compile science to generic Scene primitives before backend code.
9. Keep premium presentation separate from scientific computation.
10. Keep Scene JSON renderer-independent and versioned.
11. Add cross-domain reuse/analytical tests for new computation.
12. Change Core only for abstractions proven universal.
13. Do not claim design documents are implemented runtime features until code and validation exist.

## Success criterion

A new scientific idea should normally require new semantics/composition and tests, not another monolithic subsystem.

Spectra succeeds when scientific meaning, numerical execution, presentation, and rendering can evolve independently behind stable contracts.
