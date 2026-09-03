# Spectra Science — Public API Source Audit

Status: **source audit; no runtime API changed**.

This document inventories the current public/re-export surfaces before a future curated `spectra.sdk` facade is implemented.

## Root package

Current:

```python
import spectra
```

exports only:

```text
Scene
```

This is intentionally small and should remain small. The future SDK should not be implemented by dumping hundreds of names into root `spectra.__init__`.

## Domain infrastructure package

Current:

```python
from spectra.domains import ...
```

exports:

```text
DomainCatalog
DomainDependency
DomainDescriptor
DomainModule
DomainRegistry
DomainResolutionError
builtin_domain_catalog
```

This is already a good infrastructure facade for internal/advanced domain authors.

A future `spectra.sdk` can re-export a curated subset rather than forcing third-party packages to know the `spectra.domains.*` file layout.

## Backend package

Current:

```python
from spectra.backends import ...
```

exports:

```text
Backend
BackendCapabilities
BackendCompatibilityError
BackendSession
BlenderBackend
BlenderHandle
BlenderTimelineController
BlenderUnavailableError
IncrementalBlenderBackend
IncrementalBlenderHandle
MemoryBackend
MemoryHandle
frame_to_engine_time
validate_backend_compatibility
```

For the general scientific SDK, avoid exposing renderer-specific Blender handles/controllers by default.

A dedicated backend-author SDK or ordinary `spectra.backends` imports are more appropriate for renderer plugin developers.

## Numerical package

Current `spectra.numerics` explicitly exports:

```text
ExecutionKind
NumericalExecutionDescriptor
NumericalMethodDescriptor
NumericalPipelineDescriptor
NumericalRunRecord
NumericalSolverImplementation
NumericalSolverPolicy
NumericalSolverRegistry
NumericalSolverRequirements
ProblemPredicate
TrackedNumericalResult
fixed_step_record
run_record
```

Potential stable SDK candidates:

```text
NumericalExecutionDescriptor
NumericalMethodDescriptor
NumericalPipelineDescriptor
NumericalSolverRequirements
NumericalSolverPolicy
TrackedNumericalResult
```

More advanced/provider-author candidates:

```text
NumericalSolverImplementation
NumericalSolverRegistry
ProblemPredicate
run_record
fixed_step_record
```

Do not expose registry internals merely for convenience if third-party domain authors can use `DomainRegistry.register_numerical_solver(...)` instead.

## Experiments package

`spectra.domains.experiments` already acts as a large subject-level facade.

It exports stable-looking scientific/product values including:

```text
ParameterAxis
ParameterCase
ParameterSweep
MetricSpec
MetricValue
ExperimentResult
TrackedExperimentResult
BatchedExperimentResult
SolverComparisonResult
ConvergenceSample
ConvergenceEstimate
SolverConvergenceResult
SensitivityParameter
SensitivityEstimate
LocalSensitivityResult
UncertainParameter
WeightedSample
UncertaintyPropagationResult
CalibrationObservation
CalibrationResult
ParetoFront
MetricObjective
ExperimentArtifact
NumericalRunArtifact
artifact_to_json
artifact_from_json
```

It also exports many `...Domain` implementation classes.

A future user-facing SDK should generally expose scientific value contracts and artifact helpers, not every Domain class.

Domain/plugin authors who need explicit factories can import subject modules or later use dedicated extension SDK helpers.

## Core value candidates

Current stable-looking immutable generic values include:

```text
Vec2
Vec3
Color
Transform3D
Quaternion
CoordinateFrame3D
Bounds3D
Unit
Quantity
Dimension
Material
Scene
Timeline
```

And generic renderer-neutral primitives:

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

These are strong SDK candidates because they are cross-domain and renderer-neutral.

However `spectra.sdk` should still distinguish ordinary scientific extension authors from backend/visualization authors so the most common import surface remains understandable.

## Suggested SDK tiers

Rather than one giant flat list, use curated subfacades.

Conceptually:

```text
spectra.sdk
spectra.sdk.domain
spectra.sdk.scene
spectra.sdk.numerics
spectra.sdk.experiments
spectra.sdk.plugins        later
spectra.sdk.presentation   later
```

Python package organization may differ, but conceptual grouping is valuable.

### `spectra.sdk` top-level candidates

Keep small:

```text
DomainModule
DomainDependency
DomainRegistry
Scene
Vec2
Vec3
Quantity
Unit
```

Potentially:

```text
PresentationIntent
```

once implemented and stabilized.

### `spectra.sdk.scene`

```text
Scene
Material
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
Timeline
Transform3D
Quaternion
Color
Vec2
Vec3
Bounds3D
```

### `spectra.sdk.domain`

```text
DomainModule
DomainDependency
DomainRegistry
DomainCatalog
DomainDescriptor
DomainResolutionError
```

Whether `DomainDescriptor` belongs in public extension SDK should be revisited after plugin runtime implementation because ordinary plugin authors may only need factories/descriptors at plugin level.

### `spectra.sdk.numerics`

First public candidates:

```text
NumericalExecutionDescriptor
NumericalMethodDescriptor
NumericalPipelineDescriptor
NumericalSolverRequirements
NumericalSolverPolicy
NumericalRunRecord
TrackedNumericalResult
```

Provider-author helpers may additionally expose a supported registration wrapper rather than the raw registry class.

### `spectra.sdk.experiments`

Curate value types/artifact APIs, not implementation domains.

Suggested:

```text
ParameterAxis
ParameterCase
ParameterSweep
MetricSpec
MetricValue
ExperimentResult
TrackedExperimentResult
BatchedExperimentResult
ExperimentArtifact
NumericalRunArtifact
artifact_to_json
artifact_from_json
```

Analysis/sensitivity/calibration records can be added once their runtime batch is validated and API stability assessed.

## What should NOT be in generic SDK

Avoid by default:

```text
BlenderHandle
IncrementalBlenderHandle
BlenderTimelineController
private backend helper functions
BUILTIN_DOMAIN_FACTORIES
internal discovery scanners
DomainRegistry internal dictionaries
NumericalSolverRegistry internal dictionaries
private serialization helpers
native/GPU pointers/handles
```

## Subject APIs

The central SDK should not flatten every scientific subject into one namespace.

Prefer subject facades:

```python
from spectra.domains.physics.electromagnetism import ...
from spectra.domains.experiments import ParameterSweep
```

or future stable subject namespaces.

`spectra.sdk` is infrastructure glue, not a replacement for all subject packages.

## Plain-Python import boundary

A critical SDK acceptance criterion:

```python
import spectra.sdk
```

must work without:

```text
Blender
CUDA
Metal
WebGPU
native solver plugin
```

Do not import optional renderer/provider SDKs at facade import time.

## Lazy/optional exports

Blender-specific helpers remain in:

```python
spectra.backends
spectra.backends.blender
```

Native/GPU provider-specific APIs remain provider/plugin-local unless a generic contract is proven.

## API stability stance

Creating `spectra.sdk` is an explicit compatibility promise.

Therefore only re-export names that have:

- clear renderer-independent meaning;
- stable constructor/behavior expectations;
- real cross-domain use;
- tests;
- no imminent redesign.

Do not add a name merely because it exists today.

## First SDK implementation recommendation

After the pending runtime validation and after W1/W2 presentation contracts receive a checkpoint:

### SDK v0 proof

Implement:

```text
spectra/sdk/__init__.py
spectra/sdk/domain.py
spectra/sdk/scene.py
spectra/sdk/numerics.py
```

Re-export existing objects only. No wrappers initially unless needed for stability.

Tests:

- exact `__all__` snapshots;
- import without Blender;
- import without optional native/GPU packages;
- sample extension can use SDK facade;
- internal module moves do not appear in sample extension imports.

Then add experiments/presentation/plugin facades as their APIs stabilize.

## Success criterion

A third-party scientific module can rely on a small documented Spectra infrastructure surface and does not need to copy imports from arbitrary internal source files. At the same time, `spectra.sdk` does not become another giant monolithic namespace.