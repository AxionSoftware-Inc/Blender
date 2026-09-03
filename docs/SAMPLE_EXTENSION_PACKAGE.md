# Spectra Science — Sample Third-Party Extension Package

This document provides a concrete blueprint for an external scientific package without implementing external plugin discovery yet.

The example subject is geometric optics because it exercises semantics, units, capability reuse, explicit views, and optional presentation hints without requiring a new renderer.

## Package layout

```text
spectra-optics/
├── pyproject.toml
├── README.md
├── src/
│   └── spectra_optics/
│       ├── __init__.py
│       ├── plugin.py
│       ├── semantics.py
│       ├── geometric.py
│       ├── views.py
│       └── diagnostics.py
└── tests/
    ├── test_geometric_optics.py
    ├── test_views.py
    └── test_plugin_contract.py
```

The package should depend on the public Spectra SDK/facades once they are implemented. Until then, this file is a packaging/contract blueprint only.

## `pyproject.toml` concept

```toml
[project]
name = "spectra-optics"
version = "0.1.0"
dependencies = ["spectra-science>=0.1"]

[project.entry-points."spectra.domains"]
optics = "spectra_optics.plugin:domain_factories"
```

External entry-point discovery is not implemented yet. The important contract is that package import itself should not mutate global Spectra state.

## Semantics

Potential immutable semantic types:

```text
Ray3D
OpticalSurface
RefractiveIndex
RefractiveIndexField3D
RayTraceProblem
RayTraceResult
```

These types own scientific meaning only.

They must not contain:

- Blender objects;
- GPU handles;
- UI widgets;
- renderer material references;
- native camera settings.

## Domain split

A reasonable package could expose more than one domain.

### `physics.optics.geometric`

Provides:

```text
physics.optics.ray3d
physics.optics.optical_surface
physics.optics.ray_trace_problem
physics.optics.trace_ray
```

Possible dependencies:

```text
mathematics.vector_field3d
field_dynamics.solve_integral_curve
```

Depending on exact formulation, the module may use generic field dynamics or its own optics-specific interface/reflection operations while still reusing vector/geometry primitives.

### `physics.optics.views`

Depends on optics semantics and generic Scene contracts.

Provides explicit views such as:

```text
physics.optics.ray_path_view
physics.optics.surface_view
```

The result compiles into generic primitives:

```text
Ray path        -> Polyline
Hit points      -> PointCloud
Optical surface -> Surface
Normals         -> VectorGlyphSet
```

## Domain class concept

```python
class GeometricOpticsDomain:
    name = "physics.optics.geometric"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("physics.optics.ray3d", Ray3D)
        registry.provide("physics.optics.ray3d", Ray3D)
        registry.provide("physics.optics.trace_ray", trace_ray)
```

Important points:

- downstream dependencies use provided capability names;
- semantic registration alone is not sufficient when another domain depends on the type;
- module import performs no global registration side effects.

## Unit behavior

Example semantic boundary:

```text
position       -> length
wavelength     -> length
refractive n   -> dimensionless
frequency      -> 1/time
```

Hot loops may use SI floats after explicit conversion.

The module must not accept arbitrary numeric wavelength and silently assume nanometers.

## Explicit visualization

A ray trace may have multiple valid presentation styles:

- path only;
- path + surfaces;
- path + normals;
- path + optical power labels;
- teaching mode showing incident/reflected/refracted components.

Therefore use explicit view configuration rather than one giant canonical default.

Conceptually:

```text
RayTraceView(
    result=...,
    show_surfaces=True,
    show_normals=False,
    show_hit_points=True,
)
```

The view compiler returns a generic Scene.

## Presentation hints

The optics package may expose scientific presentation metadata such as:

```text
wavelength -> sequential/spectral quantity
angle      -> cyclic/angular quantity
optical surface -> contextual geometry
ray path   -> primary signal
```

It must not specify Blender Principled BSDF node parameters.

A cinematic preset may choose emission-like treatment in Blender, while publication mode may choose a simple high-contrast line. The scientific module should work with both.

## Diagnostics

Example reusable scientific diagnostics:

```text
path length
incident angle
refracted angle
Snell residual
energy/transmission balance if model supports it
```

Diagnostics should return semantic values/metrics suitable for the generic experiment system.

That enables:

```text
parameter sweep over lens curvature
    -> spot-size metric
    -> sensitivity
    -> calibration
    -> Pareto analysis
```

without the optics package implementing its own experiment framework.

## Optional numerical provider

An external package may include a high-performance provider, but it should be a separate concern.

Example:

```text
spectra-optics-native/
    -> optional native ray batch provider
```

It should register a stable numerical/execution role rather than force the semantic optics domain to import native bindings directly.

## Plugin descriptor concept

Future `plugin.py` may expose something conceptually like:

```python
def domain_factories():
    return (
        GeometricOpticsDomain,
        OpticsViewsDomain,
    )
```

A richer future `PluginDescriptor` may include:

```text
plugin id
plugin version
required Spectra version range
domain factories
optional native providers
optional presentation presets
```

The runtime contract should be explicit and inspectable.

## Conflict behavior

An external module must not silently replace a built-in capability.

If two packages provide the same public capability:

- catalog integration should report the conflict;
- explicit provider selection may later resolve supported competing providers;
- scientific semantics must not depend on import order.

## Test expectations

A serious third-party module should test:

### Semantics

- validation;
- unit handling;
- analytical cases.

### Capability graph

- declared dependencies load;
- provider capabilities are published;
- missing dependencies fail clearly;
- registration rollback works.

### Visualization

- renderer-neutral Scene only;
- stable primitive IDs;
- no backend imports.

### Experiments

Where useful, verify metrics work with Spectra sweeps/calibration/convergence infrastructure.

### Plugin lifecycle

Once external discovery is implemented:

- enabled package is discoverable;
- disabled package is absent;
- uninstall does not break base Spectra;
- conflict errors are deterministic.

## What a third-party package must not do

Do not:

- monkey-patch `DomainRegistry`;
- append to hidden global factory lists;
- import Blender from scientific semantics;
- duplicate the Spectra Scene implementation;
- implement a private parameter-sweep framework;
- hardcode one numerical solver if a role exists;
- rely on package import ordering;
- write files into the Spectra installation directory at import time.

## External-developer success criterion

A developer should be able to build a substantial optics package by learning:

```text
spectra.sdk
DomainModule / DomainDependency
capability publishing
scientific semantics
Scene primitives / explicit views
experiment APIs
presentation hints
```

They should not need to understand Blender backend internals, every built-in scientific domain, or Spectra's private repository structure.
