# Spectra Science — Visualization / Presentation Boundary

Status: **source-audit/design contract; no runtime code changed**.

This document fixes the boundary between semantic scientific visualization and premium presentation.

## Existing runtime truth

`VisualizationRegistry` is type-directed:

```text
semantic Python value
    -> resolve registered semantic type through MRO
    -> SceneCompiler(value)
    -> renderer-neutral Scene
```

It does not know about Blender, presentation presets, cameras, themes, UI, or product workflows.

`DomainRegistry.register_visualization(...)` and `DomainRegistry.compile_scene(...)` expose this mechanism to domains/callers.

That separation should remain.

## Base Scene responsibility

A semantic visualization compiler should answer:

> What visual geometry is scientifically meaningful for this explicit view type?

Examples:

```text
ElectricFieldView -> VectorGlyphSet / field lines
TemperatureSliceView -> scalar slice geometry
WavefunctionPhaseView -> explicit phase-aware view geometry
ConvergenceView2D -> points/curve/labels representing convergence data
```

A base Scene may include scientifically meaningful labels/material hints when the view semantics require them, but should not encode product-level styling choices.

## Presentation responsibility

Presentation answers:

> Given a scientifically correct Scene, how should it be framed and communicated?

Examples:

```text
camera framing
presentation lights
axes/grid visibility
legend layout
title/subtitle/time label
reveal staging
presentation preset
display density
quality policy
backend fallback
```

Presentation must not recalculate physics or infer domain meaning from primitive names.

## Anti-pattern: cinematic compiler variants

Avoid proliferation such as:

```text
ElectricFieldCinematicCompiler
ElectricFieldPublicationCompiler
ElectricFieldDarkLabCompiler
```

That would multiply every scientific view by every presentation style.

Preferred:

```text
ElectricFieldView
    -> one semantic compiler
    -> base Scene
    -> analysis/publication/cinematic presentation policy
```

## Anti-pattern: backend-specific domain compiler

Do not register:

```text
BlenderElectricFieldCompiler
WebGpuElectricFieldCompiler
```

The generic compiler must produce renderer-neutral Scene primitives. Backend differences are handled after Scene composition.

## Explicit view semantics still matter

Presentation is not a substitute for explicit semantic views.

For example:

```text
quantum probability density
quantum phase
real component
imaginary component
```

are different scientific views, not presentation themes.

Likewise:

```text
velocity vectors
vorticity slice
pressure surface
streamlines
```

are scientific visualization choices.

A `cinematic` preset must not silently switch pressure to vorticity or invent an isovalue.

## Suggested product flow

```text
semantic result
    ↓
choose explicit semantic view
    ↓
VisualizationRegistry.compile(view)
    ↓
base Scene
    ↓
compose_presentation(...)
    ↓
presented Scene
    ↓
BackendCapabilities negotiation
    ↓
backend
```

## Context metadata

Presentation may need semantic metadata that raw Scene geometry cannot safely reveal.

Examples:

```text
quantity name
unit
signed/non-negative/cyclic nature
preferred reference value
primary primitive ID
result fingerprint
```

This metadata should be passed explicitly as `PresentationContext` or an equivalent immutable record.

Do not infer it from IDs such as:

```text
"quantum_phase_mesh"
"temperature_surface"
```

IDs are identity, not semantic metadata.

## Presentation hints from domains

A domain/view may optionally supply conservative hints such as:

```text
quantity is cyclic
quantity is signed
primary object
preferred camera target
recommended legend unit
```

But it should not dictate renderer-native styling.

A hint is not a hard theme.

## Base Scene determinism

For the same semantic view and scientific result, the semantic compiler should be deterministic independently of presentation preset.

This allows:

```text
one solve
one semantic view
multiple presentation variants
```

without recompiling numerical results.

## Scene IDs

Scientific primitive IDs originate from the visualization compiler/domain view.

Presentation must preserve those IDs.

Presentation-created resources use separate deterministic IDs/namespaces, for example:

```text
presentation.camera.main
presentation.light.key
presentation.annotation.title
presentation.axes.primary.x
```

This prevents presentation replacement from destabilizing scientific native-object identity.

## Timeline boundary

Scientific animation belongs to the base Scene timeline.

Presentation staging may add disjoint tracks after checking animation ownership/conflicts as defined in `ANIMATION_COMPOSITION_CONTRACT.md`.

Presentation must not replace the scientific timeline.

## Backend boundary

`BackendCapabilities` describes what the renderer can express.

Capability negotiation happens after semantic compilation and presentation intent resolution.

A domain should never contain:

```python
if backend.name == "blender":
    ...
```

## MemoryBackend role

MemoryBackend is valuable because it proves the Scene/presentation pipeline can be inspected without Blender.

Phase 1 presentation should be testable against a generic Scene/MemoryBackend before native Blender polish.

## Product/API implication

A future high-level facade can expose separate operations:

```python
view = spectra.view(result, ...)
scene = spectra.compile_view(view)
presented = spectra.present(scene, intent)
rendered = spectra.render(presented, backend)
```

Exact public names are not frozen here. The separation is.

## Tests after implementation gate

- semantic compiler output does not depend on presentation preset;
- scientific IDs remain unchanged after presentation;
- presentation-owned IDs use reserved namespace;
- same base Scene supports multiple presentation variants;
- presentation-only changes do not invoke numerical solve;
- backend capability fallback does not change source semantic result;
- explicit scientific view choice remains authoritative.

## Success criterion

Adding the 100th scientific domain should not require implementing five presentation-specific compilers or renderer-specific variants.

The domain contributes semantic views; the shared presentation system contributes communication quality; the backend contributes native rendering.