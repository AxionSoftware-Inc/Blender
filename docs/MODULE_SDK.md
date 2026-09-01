# Spectra Science — Module SDK and Extension Contract

This document defines the intended extension boundary for built-in and third-party scientific modules.

The goal is that adding the 100th or 500th scientific module does not require modifying Spectra Core, Blender code, every existing subject, or a giant central registration file.

## Design target

A normal scientific module should look conceptually like:

```text
my_domain/
    semantics.py
    domain.py
    views.py          optional
    solvers.py        optional
    diagnostics.py    optional
    tests/
```

and should integrate through stable public contracts:

```text
DomainModule
DomainDependency
DomainRegistry
capabilities
VisualizationRegistry
generic Scene primitives
optional numerical solver roles
```

The module must not require renderer-specific scientific code.

## Module categories

Spectra extensions fall into several useful categories.

### Scientific semantic domain

Introduces new subject meaning, such as:

- optics;
- astronomy;
- biology;
- control systems;
- plasma physics;
- materials science.

It normally defines semantic types and composes existing math/numerical capabilities.

### Capability adapter domain

Bridges existing concepts without introducing a new solver.

Examples:

```text
solution history -> continuous field
field -> particle force
reaction heat -> thermal source
Maxwell fields -> particle dynamics
```

### Numerical provider domain

Adds an implementation for an existing stable numerical role.

Examples:

```text
ode.first_order / native_cpu.rk4
ode.first_order / cuda.rk45
poisson3d / multigrid.native
```

Scientific consumers should remain unchanged.

### Visualization/presentation extension

Adds semantic-to-Scene views or reusable presentation policies without altering scientific computation.

### Backend extension

Consumes generic `Scene`/presentation intent and maps it to a renderer or execution environment.

Backend SDK concerns must remain separate from scientific-domain SDK concerns.

## Minimal DomainModule contract

A discoverable domain should provide a zero-argument constructible class whose name ends in `Domain` and whose instance exposes conceptually:

```python
class ExampleDomain:
    name = "example.subject"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        ...
```

The current built-in auto-discovery model uses this convention to avoid maintaining a giant central factory list.

### `name`

Rules:

- stable;
- globally unique inside one Spectra environment;
- lowercase dotted namespace preferred;
- describes ownership rather than implementation technology.

Good:

```text
physics.optics.geometric
biology.reaction_networks
astronomy.orbital_dynamics
```

Avoid:

```text
new_module2
gpu_physics
blender_optics
```

### `version`

The domain version describes the bundled domain contract/version and participates in environment provenance.

Capability versions remain separate because a domain can evolve while individual public contracts remain compatible.

### `dependencies`

Depend on stable capability names, not on another domain's private module layout.

Good:

```python
DomainDependency("pde.laplacian_3d")
DomainDependency("ode.solve_first_order", min_version=4)
```

Avoid importing another subject's internal solver function merely because it exists in the same repository.

## Capability design

A capability is the public dependency boundary.

Capability names should answer **what is provided**, not **how it is currently implemented**.

Good:

```text
physics.optics.refractive_index_field3d
physics.optics.trace_ray
biology.diffusion.reaction_source
```

Implementation-specific capabilities are appropriate only when the implementation itself is intentionally selectable/discoverable, such as optional numerical providers:

```text
ode.first_order.rk45_reference
ode.first_order.native_cpu
```

### Publishing

Use `registry.provide(...)` for anything another domain is expected to depend on.

Registering a semantic type alone is not sufficient if downstream modules declare it as a `DomainDependency`.

This rule is important because the automatic DomainCatalog provider graph is generated from actual capability ownership.

### Versioning

Bump a capability version when its public contract changes in a way consumers need to require explicitly.

Do not bump merely because internals became faster.

A Python reference implementation replaced by native CPU/GPU behind the same contract should normally preserve the capability version.

## Semantic types

Semantic types represent scientific meaning before visualization/rendering.

Good examples:

```text
ParticleProblem
PotentialField3D
ChemicalReaction
MetricTensorField
ScalarPDEProblem3D
```

Semantic types should preferably be:

- immutable or treated immutably;
- unit-aware where physical dimensions matter;
- renderer-independent;
- deterministic in validation;
- explicit about coordinate systems/boundaries when scientifically necessary.

Do not store Blender objects, GPU handles, material node references, or UI widgets in semantic objects.

## Cross-domain reuse rule

Before implementing an algorithm inside a new module, search for an existing capability.

Typical reusable foundations include:

- ODE integration;
- PDE grids/operators;
- linear algebra;
- tensor algebra;
- fields;
- interpolation;
- integration;
- Poisson solvers;
- mechanics trajectories;
- generic continuity diagnostics;
- Scene views.

A new physics module should not contain its own RK4 simply because it needs time integration.

## Numerical solver providers

A module that adds a faster solver should implement the stable role rather than creating a parallel scientific API.

Conceptual registration:

```python
registry.register_numerical_solver(
    role="ode.first_order",
    implementation_id="native_cpu.rk4",
    solver=solve,
    method=method_descriptor,
    execution=execution_descriptor,
    priority=...,
    tags=(...),
    supports_problem=...,
)
```

Provider requirements are specified in:

- `docs/NATIVE_NUMERICAL_BACKENDS.md`
- `docs/NUMERICAL_BUFFERS.md`
- `docs/NUMERICAL_BACKEND_VALIDATION.md`

Do not teach scientific domains to import CUDA, C++, NumPy, Metal, WebGPU, or another execution technology.

## Visualization contract

A domain may register a default visualization only when its semantic object has a sensible canonical presentation.

Conceptually:

```python
registry.register_visualization(MySemanticType, compile_my_semantic)
```

The compiler returns generic `Scene` primitives.

Use existing primitives where possible:

```text
Point
PointCloud
Polyline
Surface
Region
VectorGlyph
VectorGlyphSet
TextLabel
Group
Camera
Light
```

Do not create renderer-native objects in a visualization compiler.

### Explicit views

Some semantics have multiple valid visualizations.

Examples:

```text
VectorField3D
  -> arrows
  -> streamlines
  -> slice

Complex wavefunction
  -> magnitude
  -> probability density
  -> phase
```

In those cases create explicit view semantics/policies rather than guessing a default renderer representation.

## Presentation extensions

A module may provide domain-aware presentation hints, but presentation must remain separate from scientific computation.

For example, a quantum view may state that phase is cyclic. It should not instantiate Blender emission shaders itself.

See `docs/PREMIUM_PRESENTATION_SYSTEM.md`.

## Units

Physical module APIs should use `Unit` / `Quantity` or field unit metadata at the semantic boundary.

Hot numerical loops may convert to SI floats internally, but conversion should happen explicitly and consistently.

Do not accept a unit-aware field and then accidentally treat raw evaluator numbers as SI without conversion.

## Error handling

Scientific contract violations should fail early and explain the semantic problem.

Examples:

- incompatible dimensions;
- grid/state length mismatch;
- invalid boundary mode;
- unknown capability;
- unsupported solver/problem combination;
- non-finite values.

Do not silently clamp/convert/change scientific semantics unless the API explicitly defines such behavior.

## Discovery model

### Built-in modules

Current built-ins are auto-discovered from `spectra.domains` using the strict Domain naming/constructor contract, then probe-registered to derive actual capability ownership.

Therefore adding a normal built-in domain should not require editing a central `BUILTIN_DOMAIN_FACTORIES` manifest.

### Third-party modules

The intended future packaging model is entry-point or explicit package discovery rather than arbitrary recursive import of the user's environment.

Conceptual Python packaging direction:

```toml
[project.entry-points."spectra.domains"]
my_optics = "my_package.spectra_plugin:domain_factories"
```

The exact external entry-point runtime is not yet implemented and should be added only after the current numerical milestone is green.

External discovery must be:

- explicit;
- deterministic;
- inspectable;
- safe to disable;
- isolated from Core semantics.

## Suggested third-party package layout

```text
spectra-optics/
    pyproject.toml
    src/
        spectra_optics/
            __init__.py
            domains/
                geometric.py
                wave.py
            views/
            data/
    tests/
```

The package should depend on `spectra-science` through its public API, not copy engine source files.

## Namespace guidance

External capability/domain names should use stable subject namespaces, not necessarily package/vendor names.

When collision risk is real, a vendor namespace may be used deliberately:

```text
acme.materials.composite_failure
```

but standard scientific concepts should preferably converge on shared community/public contracts rather than duplicate vendor-specific semantic names.

## Optional dependencies

A module may declare optional `DomainDependency` entries for enhancements that are not required for core operation.

Optional dependencies must not change the meaning of the required computation silently.

Example:

```text
required: scalar field
optional: premium presentation capability
```

is reasonable.

```text
required: approximate physics
optional: correct units
```

is not.

## Transactional registration

Domain registration is atomic. If registration fails, partial capability/solver/visualization mutations must roll back.

A module author should therefore perform registration through `DomainRegistry` rather than mutating global singleton state outside it.

Avoid side effects during module import.

## No global initialization order

Modules must not assume:

```text
math is always imported first
then physics
then visualization
```

Declare dependencies and let the catalog/registry resolve them.

This rule is what allows large module counts without fragile startup ordering.

## Renderer/backend independence checklist

A scientific module is not acceptable if it:

- imports `bpy`;
- imports a WebGPU SDK;
- creates native render objects;
- depends on Blender frame numbers;
- uses renderer coordinates as hidden physical units;
- requires a render engine to compute its numerical solution.

Backend-specific extensions belong under backend/plugin packages.

## AI-generated modules

A future AI authoring system may generate or assemble domain modules, but generated modules must obey the same deterministic contracts:

- declared capabilities;
- typed semantics;
- unit validation;
- no renderer leakage;
- tests;
- explicit solver roles;
- explicit visualization views.

AI is an authoring/compiler surface, not the scientific runtime authority.

## Minimum acceptance checklist for a new module

A new domain should normally have:

1. stable domain name/version;
2. declared capability dependencies;
3. public semantic types;
4. public provided capabilities;
5. unit/shape validation where needed;
6. reuse of existing math/numerical capabilities;
7. renderer-neutral visualization or an explicit reason none exists;
8. tests for analytical/reference behavior;
9. catalog/discovery test when introducing a new provider chain;
10. documentation of scientific limitations.

For numerical-provider modules also require:

11. method metadata;
12. execution metadata;
13. problem compatibility rules;
14. parity/convergence validation;
15. provenance coverage.

## Example: adding an optics domain

A geometric optics module might reuse:

```text
mathematics.vector_field3d
field dynamics / ODE integration
geometry intersections
units
Scene Polyline
```

and add only optics-specific semantics such as:

```text
Ray
OpticalSurface
RefractiveIndex
Snell/reflection rules
```

It should not require Blender ray objects or a new animation subsystem.

## Example: adding biology reaction transport

A biology module might reuse:

```text
chemistry ReactionNetwork
coupled PDE3D
transport/diffusion
experiments/calibration
```

and add biological semantics/kinetic laws only.

## Success criterion

A competent external developer should be able to add a serious new scientific module by learning the domain/capability/Scene contracts, without reading Blender backend internals and without modifying Spectra Core.
