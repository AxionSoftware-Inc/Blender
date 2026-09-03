# Spectra Science — Curated SDK Export Matrix

Status: **design/source-audit contract; no runtime code changed**.

This document proposes how a future `spectra.sdk` facade should be assembled from real existing runtime modules without turning the root `spectra` namespace into a giant unstable import surface.

## Existing runtime truth

Current top-level package is intentionally minimal:

```python
from spectra import Scene
```

`core/__init__.py` is empty.

Other subsystem packages already expose curated surfaces, for example:

```text
spectra.domains
spectra.backends
spectra.domains.experiments
spectra.numerics
```

This is a good starting point for an explicit SDK facade.

## Design goal

Third-party modules should not import arbitrary private paths such as:

```python
from spectra.domains.physics.some_internal_module import _helper
```

Instead they should depend on a documented compatibility surface.

The SDK should be organized by responsibility rather than flattening hundreds of names into one namespace.

## Proposed facade

```text
spectra.sdk
spectra.sdk.scene
spectra.sdk.domain
spectra.sdk.numerics
spectra.sdk.experiments
spectra.sdk.presentation
spectra.sdk.plugin
spectra.sdk.project
```

The submodules are the stable surface. `spectra.sdk` itself may re-export a small convenience subset only.

## `spectra.sdk.scene`

Strong existing candidates:

```text
Scene
Vec2
Vec3
Color
Transform3D
Quaternion
CoordinateFrame3D
Bounds3D
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
Track
Keyframe
```

Rules:

- expose renderer-neutral semantic Scene contracts;
- do not expose Blender objects/datablocks;
- avoid private serialization helpers;
- only expose bounds/camera helpers once their semantics are stable enough for extensions.

## `spectra.sdk.domain`

Existing candidates from `spectra.domains`:

```text
DomainModule
DomainDependency
DomainRegistry
DomainCatalog
DomainDescriptor
DomainResolutionError
builtin_domain_catalog
```

This is the core extension surface.

Third-party scientific modules should be able to define/register/load domains without importing built-in-domain discovery internals.

Do not expose:

```text
_active_domain_name
registry snapshots
probe implementation details
built-in recursive discovery internals
```

## `spectra.sdk.numerics`

Existing candidates from `spectra.numerics`:

```text
ExecutionKind
NumericalExecutionDescriptor
NumericalMethodDescriptor
NumericalPipelineDescriptor
NumericalRunRecord
NumericalSolverImplementation
NumericalSolverPolicy
NumericalSolverRequirements
TrackedNumericalResult
ProblemPredicate
run_record
fixed_step_record
```

Potentially **do not** initially expose `NumericalSolverRegistry` directly to ordinary extension authors if `DomainRegistry.register_numerical_solver(...)` is sufficient.

Reason:

- keeping registration through DomainRegistry preserves transactional provider ownership;
- direct solver-registry mutation is a lower-level integration path.

Advanced provider SDK may still expose it deliberately.

## `spectra.sdk.experiments`

The current experiment package already has a broad public surface.

Recommended first stable concepts should prioritize model/config/result contracts over every implementation-domain class.

Strong candidates:

```text
ParameterAxis
ParameterCase
ParameterSweep
MetricSpec
MetricValue
ExperimentResult
TrackedExperimentResult
SolverComparisonResult
ExperimentArtifact
NumericalRunArtifact
MetricObjective
ParetoFront
ConvergenceSample
ConvergenceEstimate
SolverConvergenceResult
SensitivityParameter
SensitivityEstimate
LocalSensitivityResult
WeightedSample
UncertainParameter
UncertaintyPropagationResult
CalibrationObservation
CalibrationResult
```

Artifact helpers may be exposed in an artifact submodule rather than the main experiments namespace.

Avoid promising every `...Domain` class as long-term SDK surface unless third-party authors genuinely need to instantiate it directly.

Capability-driven catalog loading is usually preferable.

## `spectra.sdk.presentation`

Not implemented yet.

Planned first candidates after Phase 1:

```text
PresentationPreset
PresentationIntent
PresentationContext
CameraPolicy
LightingPolicy
AnnotationPolicy
AnimationPolicy
QualityPolicy
ResolvedPresentation
compose_presentation
resolve_presentation
```

Do not expose Blender-specific presentation plans here.

## `spectra.sdk.plugin`

Not implemented yet.

Planned candidates:

```text
PluginDescriptor
PluginRequirement
PluginRegistry
PluginState
PluginStatus
PluginDiagnostic
```

Catalog composition helpers may be public if they are needed by application hosts.

Entry-point scanning may remain application/plugin-manager API rather than scientific-module API.

## `spectra.sdk.project`

Not implemented yet.

Planned candidates:

```text
ProjectMetadata
ModelRecord
ProjectSolverSelection
ResultRecord
ViewRecord
PresentationVariantRecord
EnvironmentRequirement
ProjectDocument
ProjectRuntime
```

Do not expose renderer-native cache handles as project API.

## Backend exports

Renderer/backend APIs already live naturally in `spectra.backends`.

Do not duplicate every Blender class into `spectra.sdk`.

A separate host/application developer may use:

```python
from spectra.backends import Backend, BackendCapabilities, BackendSession
```

Scientific third-party modules normally should not depend on renderer backends at all.

## Units

Units are a key scientific extension dependency and should receive a curated stable facade.

Potential future layout:

```text
spectra.sdk.units
```

Expose:

```text
Dimension
Unit
Quantity
canonical/common SI units
```

Do not require external modules to import a giant internal constants table unless the symbols are intentionally public.

## Stability classes

Every SDK export should be assigned one of:

```text
stable
provisional
experimental
internal
```

Initial `spectra.sdk` may launch as provisional while compatibility fixtures mature.

Once marked stable:

- names are not removed casually;
- semantic behavior is not silently reinterpreted;
- deprecation follows `API_STABILITY_POLICY.md`.

## Lazy import policy

The SDK should avoid importing Blender or optional heavy/native providers merely because a user writes:

```python
import spectra.sdk
```

Renderer/provider imports remain lazy or isolated.

Likewise, importing the SDK should not instantiate the entire DomainCatalog unless requested.

## Circular import policy

The facade must not become an architectural dependency of engine internals.

Rule:

```text
internal implementation -> never imports spectra.sdk
spectra.sdk -> imports/re-exports internal public contracts
```

This keeps the SDK one-way.

## Extension-author path

A normal third-party domain should ideally need only:

```python
from spectra.sdk.domain import DomainDependency, DomainRegistry
from spectra.sdk.scene import Scene, Polyline, Vec3
from spectra.sdk.units import Quantity, Unit
```

and optionally:

```python
from spectra.sdk.numerics import NumericalMethodDescriptor, NumericalExecutionDescriptor
```

No Blender import should be necessary.

## Acceptance tests after implementation gate

- `import spectra.sdk` does not import `bpy`;
- `import spectra.sdk` does not build the built-in catalog eagerly;
- curated submodule imports match documented names;
- no private underscored names exported;
- sample optics extension can use only SDK imports;
- SDK facade does not introduce circular imports;
- root `spectra` remains intentionally small;
- public export snapshot fixture catches accidental removals.

## Success criterion

External developers can build serious Spectra modules against a small documented compatibility surface while internal file organization remains free to evolve.