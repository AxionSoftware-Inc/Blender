# Blender Backend Contract

Blender is a renderer/backend for Spectra. It is not the scientific engine and it does not own scientific time.

## Import boundary

`bpy` and `mathutils` must remain lazy dependencies inside `spectra.backends.blender`.

The following must remain valid in ordinary Python without Blender installed:

```python
from spectra.backends import BlenderBackend, IncrementalBlenderBackend
from spectra.domains import DomainRegistry
```

Only native backend execution (`create`, `apply`, `destroy`, timeline binding) may require Blender.

## Static snapshot contract

The backend receives a renderer-neutral static `Scene`.

```text
scientific semantics
    -> Scene + Timeline
    -> Scene.sample(t)
    -> static Scene snapshot
    -> Blender backend
```

Blender frame handlers must never become the source of scientific truth.

## Backends currently present

### `BlenderBackend`

Reference implementation. Simple and conservative. It proves mapping correctness and currently rebuilds its owned scene on `apply()`.

### `IncrementalBlenderBackend`

Performance-oriented implementation. Stable Spectra primitive IDs map to stable Blender objects. It updates frequently-changing data in place when possible.

Current fast paths include:

- `Point.position` -> existing mesh vertices;
- `PointCloud.positions` -> existing batched mesh vertices;
- `Polyline.points` -> existing spline point buffer;
- `Surface.vertices` -> existing mesh vertices;
- `VectorGlyphSet.origins/vectors` -> existing multi-spline curve;
- transform/visibility-only changes -> object properties only.

Structural changes or unsupported mutations fall back to deterministic per-primitive or scene rebuild paths.

## Dense primitive rule

Never map a dense scientific primitive to one Blender object per instance.

Current mappings:

```text
PointCloud      -> one Blender mesh object
VectorGlyphSet  -> one Blender Curve object with many splines
```

Later Geometry Nodes/GPU/attribute implementations may replace the internals without changing Core semantics.

## Timeline playback

`BlenderTimelineController` maps Blender transport frames to Spectra engine time:

```text
Blender frame_current
    -> frame_to_engine_time(...)
    -> BackendSession.seek(t)
    -> Scene.sample(t)
    -> IncrementalBlenderBackend.apply(snapshot)
```

This permits normal Blender play/scrub controls while preserving engine ownership of animation semantics.

## Materials and lighting

Spectra owns renderer-neutral `Material` resources and `Light` primitives. The Blender adapter maps these to node materials and native Blender lights.

Do not expose Blender node names, material datablock names, or light objects as scientific-domain state.

## Current limitations

- Incremental Blender execution still needs a real local Blender smoke test.
- Per-instance colors in the reference batch mapping currently use bounded material slots; a shader/color-attribute path should replace this for very high color cardinality.
- Geometry Nodes/native GPU instancing are not yet used.
- Group primitives are organizational references; generic transform inheritance is not yet part of Core.
- Topology-changing animation may still require native data replacement.

## Local validation targets

When local testing resumes, run plain Python tests first, then Blender smoke examples:

```text
examples/blender_smoke.py
examples/blender_wave_animation.py
examples/blender_em_wave_animation.py
```

Validation should include create/apply/destroy cleanup, timeline scrubbing, particle PointCloud updates, wave Polyline updates, vector-field batch updates, camera framing, materials, and lights.
