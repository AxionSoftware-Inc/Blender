# Spectra domain system

This document records the modular scientific-domain architecture used by Spectra Science. Read it together with the repository `README.md` before extending the engine.

## Core rule

Spectra Core must remain small and renderer-independent. It owns generic infrastructure such as values, units, coordinate frames, scene primitives, timelines, expressions, and domain registration. It must not become a giant implementation of calculus, probability, statistics, linear algebra, mechanics, electromagnetism, quantum physics, or future scientific fields.

Scientific knowledge lives in pluggable domains.

```text
Spectra Core
  -> DomainRegistry / capability graph
      -> mathematics
      -> calculus
      -> probability
      -> linear_algebra
      -> differential_equations
      -> mechanics
      -> electromagnetism
      -> quantum
      -> future domains
  -> generic Scene
  -> renderer backend
```

## Capabilities, not implementation coupling

A domain publishes stable capabilities under names such as:

- `mathematics.vector_field3d`
- `probability.discrete_distribution`
- `linear_algebra.normalize_complex`
- `ode.solve_rk4`
- `physics.mechanics.solve_particle`

Another domain declares a `DomainDependency` on the capability it needs and resolves that capability through `DomainRegistry`. It should not copy the algorithm and should avoid importing another domain's private implementation details.

The capability contract is the dependency boundary. The implementation behind it may later move from pure Python to NumPy, SciPy, Rust, C++, GPU compute, or another implementation without forcing dependent scientific domains to be rewritten.

## Automatic dependency resolution

`DomainRegistry.add_domains(...)` accepts modules in arbitrary order and resolves the dependency graph from published capabilities. This is required for scalability: a future product may load dozens or hundreds of domains and should not depend on a manually maintained initialization sequence.

Missing providers or dependency cycles must fail with a diagnostic rather than silently degrading the scientific model.

## Current composition proofs

### Quantum physics

`QuantumDomain` depends on linear algebra and probability capabilities.

```text
linear_algebra.complex_vector
linear_algebra.normalize_complex
probability.discrete_distribution
        -> physics.quantum
```

Quantum state construction and measurement probabilities therefore reuse the mathematical domains instead of reimplementing vector normalization or probability distributions.

### Electromagnetism

`ElectromagnetismDomain` describes point charges and Coulomb electric fields, but uses the generic mathematical `VectorField3D` representation.

```text
mathematics.vector_field3d
        -> electromagnetism law
        -> VectorField3D
        -> VectorGlyph Scene
        -> Blender/WebGPU/etc.
```

A gravity field, fluid velocity field, magnetic field, or future custom field can reuse the same scene compiler.

### Mechanics

Newtonian particle mechanics depends on the differential-equations domain rather than owning a solver.

```text
ode.first_order_system + ode.solve_rk4
        -> mechanics particle problem
        -> trajectory
        -> Polyline/Point Scene
```

The current RK4 implementation is a deterministic reference solver. A more advanced adaptive/native/GPU solver can replace it behind the capability contract later.

## Units and coordinates

Physical domains must not hide units in renderer coordinates. Spectra Core now contains dimensional `Unit` / `Quantity` types and renderer-independent `CoordinateFrame3D`.

Scientific coordinates remain scientific data. A renderer backend is responsible for mapping them into Blender units, WebGPU world coordinates, Unreal coordinates, or another native representation.

## Where new subjects belong

Examples:

- calculus -> domain
- probability theory -> domain
- statistics -> domain
- linear algebra -> domain
- differential equations -> domain
- graph theory -> domain
- complex analysis -> domain
- topology -> domain if/when useful visual semantics are defined
- classical mechanics -> physics domain
- electromagnetism -> physics domain
- fluid dynamics -> physics domain, likely consuming fields + PDE/ODE capabilities
- quantum mechanics -> physics domain consuming linear algebra + probability + complex-number capabilities
- a newly invented mathematical model -> new domain/capability, without modifying core unless it reveals a truly universal missing abstraction

## Rule for changing Core

Adding a new subject is not sufficient reason to modify Core.

Core should change only when several unrelated domains reveal the same missing universal abstraction. For example, units and coordinate frames belong in Core because many mathematical and physical domains need them independently. Coulomb's law does not belong in Core because it is specific to electromagnetism.

A useful test is:

> If this scientific subject disappeared tomorrow, would the abstraction still make sense for several unrelated domains?

If no, keep it in a domain.

## Visualization rule

Domain semantics do not create Blender objects. Domain visualization compilers lower semantic objects into generic Spectra primitives such as:

- `Point`
- `Polyline`
- `Region`
- `VectorGlyph`
- `TextLabel`
- later surfaces, volumes, particles, instanced glyphs, trails, cameras, and other reusable primitives

Backends consume the generic scene.

## Long-term scalability target

The target is not merely to support a long feature list. The target is for the cost of adding the 100th scientific concept to remain controlled.

Ideally a new module consists mostly of:

1. its scientific semantic types;
2. declared capability dependencies;
3. computation/relationships specific to that subject;
4. compositions into existing visual primitives;
5. tests.

It should not require rewriting the engine, renderer, animation system, unit model, or every previously implemented subject.

## Continuation checklist

When another agent/session continues development:

1. Read `README.md` and this file.
2. Keep `spectra.core` free of subject-specific knowledge and renderer SDKs.
3. Prefer domain capabilities over cross-domain implementation imports.
4. Use `DomainRegistry.add_domains(...)` for dependency-resolved module loading.
5. Reuse existing mathematical semantics before creating new physics-specific equivalents.
6. Compile semantics to generic `Scene` primitives before touching Blender/WebGPU.
7. Add tests that demonstrate cross-domain reuse.
8. Change Core only for abstractions proven universal across domains.
