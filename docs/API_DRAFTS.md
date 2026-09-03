# Spectra Science — Concrete Runtime API Drafts

Status: **design/index only; no runtime implementation implied**.

This file indexes the concrete Python-facing API drafts prepared while the current runtime batch is awaiting local validation.

These drafts are intentionally more implementation-specific than the broader architecture documents, but their names/signatures remain provisional until the corresponding runtime phase is implemented and tested.

## 1. Presentation runtime

Source:

- `PRESENTATION_API_DRAFT.md`
- `PHASE1_PRESENTATION_IMPLEMENTATION_CHECKLIST.md`

Key proposed API:

```python
PresentationIntent
PresentationPreset
CameraPolicy
LegendPolicy
AxesPolicy
AnnotationPolicy
LightingPolicy
AnimationPolicy
QualityPolicy
PresentationContext
ResolvedPresentation
resolve_presentation(...)
compose_presentation(...)
```

Implementation phase:

```text
first runtime phase after pending numerical validation becomes green
```

Goal:

```text
base Scene + presentation intent -> renderer-neutral enriched Scene
```

## 2. Renderer capability negotiation

Source:

- `RENDERER_CAPABILITIES_API_DRAFT.md`

Key proposed API:

```python
RendererCapabilities
PresentationFallback
BackendResolvedPresentation
resolve_presentation_for_backend(...)
```

Implementation phase:

```text
after generic presentation semantics/composer are stable,
before or alongside WebGPU/multiple premium renderers
```

Goal:

```text
same presentation intent
  -> deterministic faithful renderer-specific fallback plan
```

Scientific domains remain unaware of backend identity.

## 3. Plugin runtime

Source:

- `PLUGIN_RUNTIME_API_DRAFT.md`
- `PLUGIN_PACKAGING.md`
- `MODULE_SDK.md`

Key proposed API:

```python
PluginRequirement
PluginDescriptor
PluginState
PluginRegistry
PluginLoadPlan
catalog_with_plugins(...)
```

Implementation phase:

```text
after public SDK/domain contracts are stable enough
```

First implementation intentionally uses explicit in-process descriptors. Python entry-point discovery comes later.

Goal:

```text
third-party package -> normal DomainModule factories -> same DomainCatalog/DomainRegistry
```

No second scientific runtime is introduced.

## 4. Project runtime

Source:

- `PROJECT_RUNTIME_API_DRAFT.md`
- `PROJECT_DOCUMENT_MODEL.md`
- `PROJECT_STATE_MODEL.md`

Key proposed API:

```python
ProjectMetadata
ModelRecord
SolverPolicyRecord
ResultRecord
ViewRecord
PresentationVariantRecord
EnvironmentRequirement
ProjectDocument
ProjectRuntime
project_to_dict(...)
project_from_dict(...)
```

Implementation phase:

```text
after presentation/public SDK/plugin foundations have clean checkpoints
```

Goal:

```text
renderer-independent scientific project as source of truth
```

`.blend` remains an output/workspace/cache rather than authoritative science.

## 5. Semantic introspection

Source:

- `INTROSPECTION_API_DRAFT.md`
- `SEMANTIC_METADATA_AND_INTROSPECTION.md`

Key proposed API:

```python
DomainInfo
CapabilityInfo
ParameterInfo
SemanticTypeInfo
ViewInfo
SolverRoleInfo
SolverImplementationInfo
EngineInspector
```

Implementation phase:

```text
can begin after registry contracts are validated and stable;
recommended before large generic UI/AI authoring implementation
```

Goal:

```text
100-500 domains become inspectable by UI/CLI/AI without hardcoded subject switches
```

Metadata enriches real runtime ownership; it does not replace capability/solver/view registries.

## 6. Native numerical provider

Source:

- `NATIVE_PROVIDER_API_DRAFT.md`
- `NATIVE_NUMERICAL_BACKENDS.md`
- `NUMERICAL_BUFFERS.md`
- `NUMERICAL_BACKEND_VALIDATION.md`

Key proposed API concepts:

```python
NativeProviderDescriptor
NativeSolverBinding
normal NumericalSolverRegistry registration
problem compatibility predicate
execution/provenance metadata
```

First target:

```text
ode.first_order / rk4.native_cpu
```

Implementation phase:

```text
performance track after solver-role runtime is validated green
```

Goal:

```text
native execution provider can be installed/removed without changing scientific domain APIs
```

## Dependency/order map

Recommended sequence:

```text
PENDING RUNTIME VALIDATION
        ↓
Presentation API Phase 1
        ↓
Presentation composer checkpoint
        ↓
Quantitative presentation / renderer capabilities
        ↓
Blender premium mapping

in parallel after clean numerical checkpoint:
Native CPU provider
        ↓
Buffer contract proven
        ↓
GPU provider

later product ecosystem:
Introspection
   ↓
Public SDK
   ↓
Plugin runtime
   ↓
Project runtime
   ↓
Standalone/UI/AI/remote workflows
```

The exact order of introspection/public SDK/project work may adjust after implementation feedback, but each foundational cross-cutting change should receive its own green checkpoint.

## What is deliberately not frozen yet

Do not treat the following as stable public API merely because they appear in drafts:

- module file layout;
- exact enum membership;
- exact project schema fields;
- native C ABI signatures;
- plugin entry-point group name;
- renderer capability field list;
- root `spectra` exports.

Freeze only after runtime implementation + tests demonstrate the contract.

## Compatibility principle

When these APIs are implemented, existing working flows should remain valid wherever possible:

```python
registry.compile_scene(value)
staggered_reveal(scene, ...)
registry.get("ode.solve_first_order")
existing DomainModule registration
existing Blender backend usage
```

New platform layers should be additive around the semantic engine rather than forcing an immediate rewrite of every existing caller.

## Validation discipline

For each API draft that becomes runtime code:

```text
implement one coherent layer
  -> targeted tests
  -> full pytest
  -> native Blender smoke only if Scene/backend behavior changed
  -> record new baseline
  -> proceed to next cross-cutting layer
```

Do not turn all drafts into runtime code in one giant unchecked batch.

## Current repository status reminder

The latest known runtime-code checkpoint before the documentation-only architecture block remains:

```text
00b5403a9ffb005b7eb011833174e013158ee1f4
```

The last fully reported verified runtime baseline remains:

```text
acb9e056326177fac49cc57b202ca80cca5090a7
224 passed
Blender 5.2 native PASS
```

See `CURRENT_STATUS.md` for the authoritative separation between verified, implemented-awaiting-validation, and design-only work.