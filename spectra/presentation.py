from __future__ import annotations

from spectra.core.animation import Timeline, Track, draw_track, fade_track
from spectra.core.primitives import Camera, Group, Polyline
from spectra.core.scene import Scene


def merge_timelines(*timelines: Timeline) -> Timeline:
    """Merge independent engine timelines while preserving validation rules."""
    if not timelines:
        return Timeline()
    tracks: list[Track[object]] = []
    duration = 0.0
    for timeline in timelines:
        duration = max(duration, timeline.duration)
        tracks.extend(timeline.tracks)
    return Timeline(duration=duration, tracks=tuple(tracks))


def staggered_reveal(
    scene: Scene,
    *,
    start_time: float = 0.0,
    item_duration: float = 0.6,
    stagger: float = 0.12,
    include_groups: bool = False,
) -> Scene:
    """Apply a renderer-neutral reveal animation to an existing Scene.

    Polylines are drawn through trim animation; other visual primitives fade in.
    Cameras are presentation controls rather than visible scene content and are
    never included in automatic reveal effects.
    """
    if start_time < 0.0:
        raise ValueError("start_time cannot be negative")
    if item_duration <= 0.0:
        raise ValueError("item_duration must be positive")
    if stagger < 0.0:
        raise ValueError("stagger cannot be negative")

    tracks: list[Track[object]] = []
    end_time = scene.timeline.duration
    reveal_index = 0
    for primitive in scene.primitives:
        if isinstance(primitive, Camera):
            continue
        if isinstance(primitive, Group) and not include_groups:
            continue
        item_start = start_time + reveal_index * stagger
        item_end = item_start + item_duration
        reveal_index += 1
        end_time = max(end_time, item_end)

        if isinstance(primitive, Polyline):
            tracks.append(
                draw_track(
                    primitive.id,
                    start_time=item_start,
                    end_time=item_end,
                )
            )
        else:
            tracks.append(
                fade_track(
                    primitive.id,
                    start_time=item_start,
                    end_time=item_end,
                )
            )

    reveal_timeline = Timeline(duration=end_time, tracks=tuple(tracks))
    return Scene(
        primitives=scene.primitives,
        timeline=merge_timelines(scene.timeline, reveal_timeline),
        frame=scene.frame,
        active_camera_id=scene.active_camera_id,
    )
