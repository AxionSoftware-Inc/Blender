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

Reference implementation. Simple and conservative. It proves mapping correctness and may rebuild owned scene structures on `apply()` where the incremental path is not used.

### `IncrementalBlenderBackend`

Performance-oriented implementation. Stable Spectra primitive IDs map to stable Blender objects. It updates frequently-changing data in place when topology is compatible.

Current fast paths include:

- `Point.position` -> existing mesh vertices;
- `PointCloud.positions` -> existing batched mesh vertices;
- `Polyline.points` -> existing spline point buffer;
- `Surface.vertices` -> existing mesh vertices;
- `VectorGlyphSet.origins/vectors` -> existing multi-spline curve;
- transform/visibility-only changes -> object properties only.

Structural changes or unsupported mutations fall back to deterministic rebuild paths.

## Dense primitive rule

Never map a dense scientific primitive to one Blender object per instance.

Current mappings:

```text
PointCloud      -> one Blender mesh object
VectorGlyphSet  -> one Blender Curve representation with many splines
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

## Native validation status

The reference/incremental Blender path has been validated on **Blender 5.2.0 LTS** in the verified `acb9e056...` milestone.

Native validation covered:

- importing Spectra inside Blender embedded Python;
- static curve/surface/material/light/camera creation;
- wave animation with real geometry changes;
- E/B `VectorGlyphSet` animation;
- stable Blender object identity;
- stable mesh/curve datablock identity when topology is unchanged;
- topology-change fallback;
- `destroy()` cleanup returning Spectra-owned datablock counts to baseline;
- 10k `PointCloud` batching without creating 10k Blender objects;
- 10k `VectorGlyphSet` batching without creating 10k Blender objects;
- 121-frame scrub/leak test with stable object/data counts.

Reference measurements from that machine included roughly:

```text
10k PointCloud create: ~199 ms
10k PointCloud update: ~96-97 ms
```

These numbers characterize the current Blender/Python/native-API path on one machine. They are not general renderer performance claims and are not numerical GPU benchmarks.

## Blender embedded-Python path note

On the validated Windows installation, setting `PYTHONPATH` outside Blender did not automatically make the repository importable inside embedded Python. Validation inserted the repository root into `sys.path` explicitly before importing Spectra.

This is launcher/environment behavior rather than a scientific-engine dependency.

Packaging/install tooling should eventually remove the need for manual path insertion.

## Current limitations

- Per-instance colors in the reference batch mapping currently use bounded material/native mechanisms rather than a final high-cardinality shader/attribute design.
- Geometry Nodes/native GPU instancing are not yet the primary dense representation.
- Group primitives are organizational references; generic transform inheritance is not yet a universal Core contract.
- Topology-changing animation may require native data replacement.
- Large-scene stress, undo/save/reload workflows, long interactive sessions, and device/render-engine-specific behavior need broader validation before calling the backend production-ready.
- The measured 10k update path leaves meaningful optimization headroom; bulk APIs, attributes, Geometry Nodes, or another renderer may improve it substantially.

## Regression expectations

When backend code changes materially, validate in this order:

1. ordinary Python import boundary;
2. full plain-Python test suite;
3. static Blender smoke;
4. animated wave/field smoke;
5. native object/datablock identity;
6. cleanup/orphan behavior;
7. dense batching;
8. repeated-frame leak test;
9. targeted performance measurements when the changed code affects hot paths.

Backend-independent scientific changes do not require rerunning the entire native Blender benchmark unless their compiled Scene behavior changes.

## Smoke examples

Existing smoke/example entry points include:

```text
examples/blender_smoke.py
examples/blender_wave_animation.py
examples/blender_em_wave_animation.py
```

These should remain thin consumers of Spectra semantics/backends. Scientific formulas must not migrate into Blender-specific example/controller code.
