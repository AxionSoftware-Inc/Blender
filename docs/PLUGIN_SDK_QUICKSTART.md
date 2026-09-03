# Spectra Science — Third-Party Plugin SDK Quickstart

Status: **developer quickstart for the planned plugin runtime; plugin manager/public `spectra.sdk` facade are not implemented yet**.

This guide shows the intended minimal path for adding a new scientific subject without editing Spectra Core or Blender backend code.

The example uses geometric optics.

## Goal

A third-party package should contribute:

```text
semantic types
+ capabilities
+ optional visualization compilers
+ optional numerical solver providers
```

through the same `DomainModule` / `DomainCatalog` / `DomainRegistry` model used by built-ins.

No second plugin-specific scientific runtime is allowed.

## Package layout

Recommended first package shape:

```text
spectra-optics/
  pyproject.toml
  src/
    spectra_optics/
      __init__.py
      domain.py
      models.py
      compute.py
      views.py
      plugin.py
  tests/
    test_optics_domain.py
    test_optics_views.py
```

## Step 1 — define semantic value types

Example:

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Ray:
    origin: Vec3
    direction: Vec3

@dataclass(frozen=True, slots=True)
class RayTraceProblem:
    rays: tuple[Ray, ...]
    max_distance: float

@dataclass(frozen=True, slots=True)
class RayTraceSolution:
    paths: tuple[tuple[Vec3, ...], ...]
```

Rules:

- immutable where practical;
- finite/unit validation belongs here;
- no Blender objects;
- no renderer material/node references;
- semantic names are independent of UI labels.

## Step 2 — implement the scientific capability

```python
def solve_raytrace(problem: RayTraceProblem) -> RayTraceSolution:
    ...
```

If the subject can reuse existing Spectra capabilities, declare that dependency instead of copying algorithms.

Examples:

```text
linear algebra
ODE integration
units/quantities
field interpolation
```

## Step 3 — define the Domain

Conceptual:

```python
from spectra.domains import DomainDependency, DomainRegistry

class OpticsDomain:
    name = "optics.raytrace"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("optics.raytrace.problem", RayTraceProblem)
        registry.register_semantic_type("optics.raytrace.solution", RayTraceSolution)

        registry.provide("optics.raytrace.problem", RayTraceProblem)
        registry.provide("optics.raytrace.solution", RayTraceSolution)
        registry.provide("optics.raytrace.solve", solve_raytrace)
```

The domain must be zero-argument constructible for catalog probing/discovery conventions.

## Step 4 — declare dependencies by capability

If ray propagation reuses an ODE capability:

```python
class OpticsDomain:
    dependencies = (
        DomainDependency("ode.solve_first_order", min_version=4),
    )
```

Do not import a private RK4 implementation and call it directly.

Capability dependency means execution can later switch between reference/native/GPU providers without changing optics source.

## Step 5 — define an explicit view

Scientific semantic objects should not automatically become arbitrary Blender geometry.

Example view:

```python
@dataclass(frozen=True, slots=True)
class RayPathView:
    solution: RayTraceSolution
    width: float = 0.01
```

Compiler:

```python
def compile_ray_path_view(view: RayPathView) -> Scene:
    return Scene(
        primitives=tuple(
            Polyline(
                id=f"optics.ray.{index}",
                points=path,
                width=view.width,
            )
            for index, path in enumerate(view.solution.paths)
        )
    )
```

Then register visualization:

```python
registry.register_semantic_type("optics.raytrace.path_view", RayPathView)
registry.provide("optics.raytrace.path_view", RayPathView)
registry.register_visualization(RayPathView, compile_ray_path_view)
```

The compiler returns generic `Scene`, not Blender objects.

## Step 6 — provide presentation metadata/hints, not renderer code

A future metadata contract may say:

```text
quantity semantics
preferred color class
recommended camera style
view category
```

Do not write:

```python
if backend == "blender":
    ...
```

inside the optics domain/view.

Premium presentation is applied after semantic visualization.

## Step 7 — plugin descriptor

Planned plugin runtime concept:

```python
PluginDescriptor(
    plugin_id="org.example.spectra_optics",
    version="1.0.0",
    display_name="Spectra Optics",
    domain_factories=(OpticsDomain,),
)
```

Descriptor construction must be side-effect free.

No solve, network access, native library load, or project mutation should occur merely because metadata is inspected.

## Step 8 — catalog composition

Planned activation path:

```text
built-in domain factories
+ enabled plugin domain factories
        ↓
DomainCatalog.from_factories(...)
        ↓
probe actual register/provide calls
        ↓
validate duplicate names/providers/dependencies
        ↓
activate candidate catalog
```

The plugin does not manually write a duplicate capability manifest.

## Step 9 — capability-driven loading

Application can request:

```text
optics.raytrace.solve
```

Catalog should load the provider and required dependency closure into `DomainRegistry`.

User/application does not need to know registration order.

## Step 10 — tests

Minimum plugin tests:

```text
domain zero-arg construction
unique domain name
registration succeeds in isolated registry
provided capability exists
semantic validation
analytical/simple ray case
view compiles to Scene
scientific IDs deterministic
no bpy import
catalog probe succeeds with built-ins + plugin
capability-driven load resolves dependencies
plugin disabled -> capability unavailable in fresh environment
```

## Optional numerical provider

A plugin may also add a solver implementation through normal registration:

```python
registry.register_numerical_solver(
    role="ode.first_order",
    implementation_id="my_solver.cpu",
    solver=my_solver,
    method=...,
    execution=...,
    supports_problem=...,
)
```

Do not create a private solver selector inside the plugin.

## Plugin identity vs domain identity

One plugin may contain multiple domains:

```text
plugin: org.example.spectra_optics

domains:
  optics.raytrace
  optics.lenses
  optics.interference
```

Do not force plugin ID and domain name to be identical.

Both identities must remain stable once public projects depend on them.

## Units

Use Spectra `Dimension`, `Unit`, and `Quantity` rather than inventing plugin-specific unit wrappers.

For inputs:

- validate expected dimension;
- convert to SI when numerical formula expects SI;
- preserve useful display unit metadata where appropriate.

## Expressions/callables

Do not serialize arbitrary Python callables into project files.

If a semantic type accepts a Python callable for in-process authoring, its project persistence contract must explicitly state whether/how it can be represented declaratively.

## Project requirements

A project using the plugin may persist:

```text
plugin_id = org.example.spectra_optics
version constraint
required capability = optics.raytrace.solve
```

Opening the project without the plugin:

- must not auto-install it;
- must not execute payload code;
- should report `plugin.missing_required_plugin` / environment requirement diagnostics;
- may still allow safe metadata inspection.

## Public SDK migration

Today the conceptual examples use current module paths such as:

```python
from spectra.domains import DomainDependency, DomainRegistry
```

Once `spectra.sdk` is implemented, third-party documentation should migrate to curated imports such as:

```python
from spectra.sdk.domain import DomainDependency, DomainRegistry
from spectra.sdk.scene import Scene, Polyline, Vec3
```

The quickstart should then be updated to avoid private/internal paths.

## Common mistakes

Do not:

1. edit the central built-in factory list;
2. copy RK4/PDE algorithms into the plugin;
3. import `bpy` in scientific code;
4. return Blender objects from a visualization compiler;
5. use display labels as stable IDs;
6. create random Scene primitive IDs every compile;
7. silently convert incompatible units;
8. claim native/GPU support without execution metadata and validation;
9. install/enable code because a project requests it;
10. bypass normal DomainRegistry registration.

## 20-minute developer mental model

If a developer remembers only this:

```text
1. define immutable science
2. reuse stable capabilities
3. register through one Domain
4. expose explicit views -> generic Scene
5. package Domain factory through plugin descriptor
6. let catalog/registry resolve dependencies
7. let presentation/backend handle visuals/rendering
```

they are aligned with Spectra architecture.

## Success criterion

Adding a new scientific subject should feel like extending a platform, not editing a monolithic Blender addon. The plugin contributes science and explicit views; the central engine keeps units, capabilities, solver selection, experiments, presentation, project state, and renderer boundaries consistent.