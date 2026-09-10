# Dynamic Quantitative Timeline — Schema Boundary and Plan

## Why this exists

Spectra can currently animate topology-stable scalar surfaces through `Surface.vertices` and can independently attach quantitative `VisualAttribute` data to a static `Surface`.

A correct time-dependent quantitative surface needs both to evolve together:

```text
scientific scalar state(t)
    -> geometry/display height(t)
    -> scalar VisualAttribute(t)
    -> presentation color mapping using one stable range
    -> display_color(t)
    -> renderer-native color buffer update
```

The missing part is not a Blender shader. It is a renderer-neutral Timeline/persistence contract for changing visual attributes.

## Current verified constraints

Current Scene v5 serialization supports `VisualAttributeSet` on primitives, but generic animation value encoding does not serialize a `VisualAttributeSet` as a Timeline keyframe value.

Therefore this tempting implementation is **not yet a valid persistent Scene-v5 contract**:

```text
Track(
    target_id="surface",
    property_path="attributes",
    keyframes=(VisualAttributeSet(...), ...),
)
```

It could work in-memory with `step` interpolation, but saved Scene/project round-trip would fail. Do not ship such a hidden runtime-only path.

## Required design properties

A future dynamic-quantitative implementation must guarantee:

1. scalar scientific values remain available at every sampled time;
2. units and `quantity_id` survive Timeline and JSON round-trip;
3. one resolved color range can cover the intended time interval, avoiding misleading frame-by-frame range breathing by default;
4. presentation-generated `display_color` does not replace the source scalar values;
5. Scene recomposition can change presentation palette/range without recomputing the scientific solve;
6. Blender/WebGPU consume the same sampled Scene semantics;
7. geometry and color samples cannot silently drift out of sync;
8. no renderer recomputes pressure, temperature, probability density, or other science from geometry.

## Recommended implementation direction

Prefer an explicit typed animation value rather than teaching arbitrary dataclass interpolation to Core.

One reasonable future shape is conceptually:

```text
AnimatedVisualAttributeFrame
    scalar_attributes: VisualAttributeSet
```

or a dedicated attribute-track structure owned by Scene/Timeline.

The exact public type should be selected through the Scene schema evolution process, not introduced ad hoc in one scientific domain.

## Interpolation policy

For the first persistent version, exact sampled scientific frames should use `step` semantics for quantitative attributes.

If geometry is derived from the same state, geometry should use the same sampled-time policy unless a scientifically explicit interpolation contract exists.

Smooth visual interpolation can be added later as presentation behavior, but must not be confused with an additional solver state.

## Color-range policy across time

For time-dependent quantitative color, default resolution should normally be based on the full intended time interval:

```text
all scalar frames
    -> one min/max or symmetric range
    -> one legend
    -> every frame mapped through that same range
```

This avoids a constant-valued color appearing to mean different physical magnitudes at different times.

A frame-local/auto-rescaled mode may exist later, but it must be explicit and visibly labeled.

## Schema/persistence gate

Before implementing dynamic attribute tracks:

- follow `docs/SCENE_SCHEMA_EVOLUTION_CHECKLIST.md`;
- decide whether the change is a Scene-v5 compatible extension or requires Scene v6;
- add serialization round-trip tests before domain/showcase adoption;
- preserve backward reading of supported older Scene versions;
- update schema/versioning documentation.

Do not bump the Scene schema solely because one showcase wants animated colors; the contract should be generic enough for pressure, temperature, concentration, probability density, stress, and future scalar quantities.

## Backend gate

After renderer-neutral persistence is green, validate:

```text
sample(t0) -> native color buffer A
sample(t1) -> native color buffer B
```

with:

- stable object identity;
- stable mesh/datablock identity when topology is unchanged;
- stable material identity;
- bounded object count;
- cleanup;
- source scalar attributes still present in sampled Scene data.

`QuantitativeBlenderBackend` already provides the static native color-attribute path; the future work should extend the generic time semantics rather than inventing a second Blender-only scientific path.

## Showcase adoption order

Once the generic contract is validated, upgrade in this order:

1. Quantum probability/phase evolution;
2. Thermoelastic temperature/deformation history;
3. reference CFD pressure/speed surface animation;
4. heat/reaction-diffusion concentration animation;
5. other time-dependent scalar scientific views.

Until then, a showcase may intentionally present a **final quantitative snapshot** while still using a real time-dependent scientific solve. It must label that distinction honestly.
