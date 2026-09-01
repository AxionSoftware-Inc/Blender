# Spectra Science — Public SDK Facade

This document defines the intended curated public import surface for external Spectra module/backend/plugin authors.

The facade is not yet implemented. The purpose of this design is to prevent third-party extensions from depending on arbitrary internal repository paths that may evolve.

## Goal

External code should eventually be able to import stable contracts conceptually through:

```python
from spectra.sdk import ...
```

rather than learning the entire internal package layout.

The facade should expose **contracts**, not every implementation helper.

## Why a facade is needed

Without a curated SDK, external modules may begin importing paths such as:

```text
spectra.domains.some_private_file
spectra.backends.blender.backend._internal_helper
```

Those imports become accidental public API and make internal refactors risky.

A deliberate SDK gives Spectra freedom to reorganize internals while preserving extension compatibility.

## SDK categories

The facade should be organized conceptually into a few small groups.

### Domain authoring

Likely public contracts:

```text
DomainDependency
DomainRegistry
DomainResolutionError
```

Potential helper protocols/base types may be added when they are stable and useful.

### Core scientific values

Likely public contracts:

```text
Vec2
Vec3
Color
Transform3D
CoordinateFrame3D
Bounds3D
Dimension
Unit
Quantity
```

Only broadly reusable stable types should be exposed.

### Scene and animation

Likely public contracts:

```text
Scene
Timeline
Track
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
Material
```

Public animation helper functions may be included when stable.

### Visualization

Likely public contracts:

```text
VisualizationRegistry
VisualizationCompileError
SceneCompiler protocol/type alias
```

Module authors should be able to register semantic -> Scene compilers without importing renderer code.

### Numerical providers

Likely public contracts:

```text
NumericalMethodDescriptor
NumericalPipelineDescriptor
NumericalExecutionDescriptor
NumericalRunRecord
TrackedNumericalResult
NumericalSolverRequirements
NumericalSolverPolicy
NumericalSolverImplementation
```

Provider registration itself remains available through `DomainRegistry`.

### Presentation

Once implemented/stabilized, likely public contracts may include:

```text
PresentationIntent
PresentationPreset
CameraPolicy
ColorScalePolicy
LegendPolicy
AnimationPolicy
QualityPolicy
```

The SDK should expose renderer-neutral presentation contracts only.

### Plugin packaging

Future public packaging contracts may include:

```text
PluginDescriptor
PluginCompatibility
plugin/domain factory protocols
```

## What should not be in the SDK

Avoid exporting:

- Blender `bpy` helpers;
- backend-private native object mapping functions;
- internal auto-discovery implementation details;
- catalog probe internals;
- private finite-difference helper loops unless intentionally public numerical APIs;
- test helpers;
- internal file-layout-specific utilities.

A function being useful inside the repo is not sufficient reason to make it public SDK.

## Scientific-domain public APIs

The SDK facade is not necessarily the only public API.

Subject packages may continue exposing their scientific semantics through stable domain package imports, for example conceptually:

```python
from spectra.domains.physics.mechanics import ParticleProblem
```

The SDK should focus on **extension-building infrastructure** shared across subjects.

A future higher-level user API may have a separate facade from the module-author SDK.

## Compatibility levels

It is useful to distinguish:

### Stable SDK

Contracts external plugin authors may rely on across compatible releases.

### Public but evolving scientific API

Domain semantics available to users but not yet guaranteed stable over long periods in pre-alpha.

### Internal

No compatibility promise.

Documentation should state these levels clearly once external releases begin.

## Version strategy

The Python distribution version alone is not enough for extension compatibility.

Future plugin compatibility may refer to a stable SDK API level/range.

Conceptually:

```text
Spectra package version: 0.4.0
SDK API level: 2
Scene schema: 5
project schema: 1
```

These evolve for different reasons.

Do not expose one integer as a fake universal version for every subsystem.

## Import stability

Once `spectra.sdk` exports a contract as stable, moving its internal implementation should not break:

```python
from spectra.sdk import DomainDependency
```

The facade re-export can remain stable while source modules are reorganized.

## Optional features

SDK import itself should not require Blender, CUDA, WebGPU, or other optional runtimes.

Bad:

```python
import spectra.sdk
# fails because bpy is unavailable
```

The base SDK must preserve plain-Python importability.

Renderer/device-specific SDKs may use separate namespaces later, for example conceptually:

```text
spectra.sdk
spectra.backends.blender.sdk
```

if a real need appears.

## Type-checking and documentation

A curated facade improves:

- IDE autocomplete;
- API reference generation;
- static type checking;
- examples;
- compatibility testing.

The project should eventually test that all documented SDK exports import successfully in ordinary Python.

## Deprecation policy

After a stable SDK begins being used externally:

1. avoid abrupt removal;
2. add documented deprecation;
3. provide replacement path;
4. keep compatibility for an announced window;
5. test the old import if it remains supported.

Pre-alpha internals may evolve faster, but once plugin ecosystem exists, accidental breaking changes become expensive.

## Example extension imports

A scientific domain plugin should eventually look like:

```python
from spectra.sdk import (
    DomainDependency,
    DomainRegistry,
    Scene,
    Polyline,
    Vec3,
)
```

A numerical provider might use:

```python
from spectra.sdk import (
    DomainDependency,
    DomainRegistry,
    NumericalMethodDescriptor,
    NumericalExecutionDescriptor,
)
```

Neither should need to import Blender internals.

## High-level user API is separate

A future end-user authoring facade may be more ergonomic:

```text
spectra.study(...)
spectra.solve(...)
spectra.present(...)
```

That user-facing API should be layered over semantic/project contracts.

Do not overload the low-level module SDK with every product convenience function.

## Implementation phases

### Phase 1

Inventory current public contracts actually used by built-in domains/providers.

### Phase 2

Create `spectra/sdk.py` or `spectra/sdk/__init__.py` with a conservative minimal export set.

### Phase 3

Add import-boundary tests in plain Python.

### Phase 4

Update module examples/docs to use the facade.

### Phase 5

Add explicit SDK compatibility/version metadata before external plugin distribution is promoted.

## Success criterion

A third-party module author should be able to build against a small documented Spectra SDK without depending on repository-private implementation paths or renderer/device internals.
