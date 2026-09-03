from __future__ import annotations

from dataclasses import replace

from spectra.core.animation import Timeline, Track, draw_track, fade_track
from spectra.core.primitives import Camera, Group, Light, Polyline
from spectra.core.scene import Scene
from spectra.core.framing import fit_camera_to_scene
from spectra.core.primitives import TextLabel, Light
from .presentation_models import (
    PresentationContext, PresentationIntent, ResolvedPresentation, RevealMode,
    LightingMode, resolve_presentation,
)


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
    """Apply a renderer-neutral reveal animation to visible content.

    Cameras and lights are presentation controls and are not automatically
    revealed. ``dataclasses.replace`` preserves future Scene-level resources so
    this helper does not need to be rewritten whenever Scene gains a new field.
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
        if isinstance(primitive, (Camera, Light)):
            continue
        if isinstance(primitive, Group) and not include_groups:
            continue
        item_start = start_time + reveal_index * stagger
        item_end = item_start + item_duration
        reveal_index += 1
        end_time = max(end_time, item_end)

        if isinstance(primitive, Polyline):
            tracks.append(draw_track(primitive.id, start_time=item_start, end_time=item_end))
        else:
            tracks.append(fade_track(primitive.id, start_time=item_start, end_time=item_end))

    reveal_timeline = Timeline(duration=end_time, tracks=tuple(tracks))
    return replace(scene, timeline=merge_timelines(scene.timeline, reveal_timeline))


def compose_presentation(
    scene: Scene,
    intent: PresentationIntent | str = PresentationIntent(),
    *,
    context: PresentationContext | None = None,
) -> Scene:
    """Compose deterministic, renderer-neutral presentation resources."""
    resolved = resolve_presentation(intent)
    context = context or PresentationContext()
    scientific = tuple(p for p in scene.primitives if not p.id.startswith("presentation."))
    scientific_scene = replace(scene, primitives=scientific, active_camera_id=(
        scene.active_camera_id if scene.active_camera_id in {p.id for p in scientific} else None
    ))
    additions = []
    if resolved.camera.mode.value == "fit_primary" and context.primary_primitive_id:
        target = scientific_scene.get(context.primary_primitive_id)
        camera_scene = replace(scientific_scene, primitives=(target,))
    else:
        camera_scene = scientific_scene
    camera = fit_camera_to_scene(
        camera_scene, padding=1.0 + resolved.camera.padding,
        camera_id="presentation.camera.primary", projection=resolved.camera.projection,
        aspect_ratio=resolved.camera.aspect_ratio, fov_y_radians=resolved.camera.fov_y_radians,
    )
    additions.append(camera)
    if resolved.lighting.mode != LightingMode.UNLIT_DATA:
        additions.append(Light(id="presentation.light.key", light_type="directional", intensity=1.0))
        if resolved.lighting.mode in {LightingMode.SCIENTIFIC_STUDIO, LightingMode.RIM_EMPHASIS}:
            additions.append(Light(id="presentation.light.fill", light_type="ambient", intensity=0.35))
        if resolved.lighting.mode == LightingMode.RIM_EMPHASIS:
            additions.append(Light(id="presentation.light.rim", light_type="directional", intensity=0.5))
    title = context.title or resolved.annotations.title
    subtitle = context.subtitle or resolved.annotations.subtitle
    if title:
        additions.append(TextLabel(id="presentation.title.primary", text=title, position=camera.transform.translation))
    if subtitle:
        additions.append(TextLabel(id="presentation.annotation.subtitle", text=subtitle, position=camera.transform.translation))
    if resolved.annotations.show_time and scene.timeline.duration > 0:
        additions.append(TextLabel(id="presentation.annotation.time", text="t = 0", position=camera.transform.translation))
    output = replace(
        scene, primitives=(*scientific, *additions),
        active_camera_id=camera.id,
    )
    if resolved.animation.reveal == RevealMode.STAGGERED:
        output = staggered_reveal(output, duration=resolved.animation.reveal_duration, stagger=resolved.animation.stagger)
    return output


__all__ = ["merge_timelines", "staggered_reveal", "compose_presentation"]
