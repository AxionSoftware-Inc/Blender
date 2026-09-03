# Spectra Science — Animation Composition and Ownership Contract

Status: **design/source-audit contract; no runtime code changed**.

This document records a concrete constraint discovered while auditing the existing `Timeline` and presentation helpers.

## Existing runtime truth

`Timeline` requires at most one track for each pair:

```text
(target_id, property_path)
```

Duplicate tracks are rejected during `Timeline` construction.

This is a good invariant: two independent systems must not silently compete to own the same animated property.

The existing `merge_timelines()` helper concatenates tracks and relies on this invariant. Therefore a conflict is explicit rather than resolved by ordering.

## Consequence for presentation

Presentation animation cannot assume that every scientific primitive is free to animate:

```text
opacity
trim_end
transform.translation
transform.rotation
...
```

For example, `staggered_reveal()` currently uses:

```text
Polyline -> trim_end
other visible primitives -> opacity
```

If a scientific timeline already owns that same property on that primitive, naive presentation merge must not overwrite it.

## Ownership classes

Conceptually classify animation tracks as:

```text
scientific
presentation
renderer-cache/internal
```

Only scientific and presentation tracks belong in the generic Spectra Timeline.

Renderer-native animation/cache state must be derived from those tracks, not become a competing source of truth.

## Phase 1 rule

Before adding any presentation track, the composer should inspect existing track keys:

```python
existing = {
    (track.target_id, track.property_path)
    for track in scene.timeline.tracks
}
```

Then use an explicit policy.

Recommended default:

```text
scientific ownership wins
```

If the requested reveal conflicts with an existing scientific track:

1. do not overwrite the scientific track;
2. do not silently change scientific animation semantics;
3. either skip the presentation effect for that primitive and record a diagnostic/fallback;
4. or fail if the requested presentation effect was marked required.

## Do not solve conflict by last-write-wins

Avoid designs such as:

```text
presentation track appended later -> wins
scientific track appended later -> wins
```

They make output depend on tuple ordering rather than explicit semantics.

## Do not multiply opacity implicitly in Timeline

A tempting solution is to keep both:

```text
scientific opacity
presentation opacity
```

and multiply them at render time.

Do not add this behavior implicitly to the existing primitive `opacity` property.

If composable channels are later needed, introduce explicit presentation/display channels or a resolved-composition stage with clear semantics and schema consequences.

## Safe first presentation properties

Presentation-owned resources such as a generated camera, generated lights, title labels, axes, and legend objects have deterministic IDs owned by presentation.

Their tracks are naturally safe because scientific domains should not target those IDs.

Therefore Phase 1 should prefer animating **presentation-created resources** over taking ownership of scientific primitive properties.

Examples:

```text
presentation.camera.main / transform
presentation.annotation.title / opacity
presentation.annotation.time / text or opacity
presentation.light.key / intensity
```

Scientific primitive reveal remains optional/best-effort when no property conflict exists.

## Polyline reveal

Current `draw_track()` owns:

```text
trim_end
```

This is safe for a static scientific Polyline with no existing trim animation.

If the scientific visualization already uses trim to encode a real scientific process or path progression, presentation must not reuse it merely for decorative reveal.

## Camera animation

If presentation creates its own deterministic camera ID, camera motion can safely own:

```text
transform.translation
transform.rotation
```

If policy preserves an existing scientific/user camera, presentation should inspect track ownership before adding camera motion.

## Time domains

Scientific evolution and presentation staging may share one engine time axis in the current Timeline contract, but their semantic roles differ.

Initial implementation may compose them on the same axis when explicitly requested.

Longer-term presentation sequencing may need a mapping such as:

```text
presentation time -> scientific sample time
```

Do not redesign Timeline for this before real showcase requirements demonstrate the need.

## Suggested helper API after validation gate

A small pure helper can make conflict behavior explicit:

```python
@dataclass(frozen=True)
class TrackConflict:
    target_id: str
    property_path: str
    existing_owner: str
    requested_owner: str


def merge_timelines_checked(
    *timelines: Timeline,
    conflict_policy: str = "error",
) -> Timeline:
    ...
```

However Phase 1 may remain simpler: presentation composer checks conflicts before calling the existing `merge_timelines()`.

Do not change the existing helper merely to hide presentation-specific semantics inside a generic function.

## Diagnostics

Presentation fallback should be inspectable, for example:

```text
presentation_animation_conflict
  target: field.line.12
  property: trim_end
  resolution: skipped decorative draw reveal
  reason: scientific timeline already owns property
```

This is preferable to a raw duplicate-track `ValueError` reaching product UI.

## Tests after implementation gate

- merging disjoint scientific/presentation tracks succeeds;
- duplicate `(target_id, property_path)` remains rejected by generic Timeline;
- composer detects opacity conflict before merge;
- composer detects Polyline trim conflict before merge;
- presentation-created camera animation composes safely;
- skipping a preferred reveal preserves scientific track exactly;
- required conflicting effect produces structured failure;
- repeated composition remains deterministic.

## Architectural conclusion

The existing strict Timeline uniqueness rule should be preserved.

Premium presentation should adapt to it rather than weaken it.

The core rule is:

> one property has one authoritative generic animation track; presentation may decorate only where it owns the property or can do so without colliding with scientific semantics.
