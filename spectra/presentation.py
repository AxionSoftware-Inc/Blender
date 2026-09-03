from __future__ import annotations

from dataclasses import replace

from spectra.color_scales import colorize_scene
from spectra.core.animation import Timeline, Track, draw_track, fade_track
from spectra.core.framing import fit_camera_to_scene
from spectra.core.primitives import Camera, Group, Light, Polyline, TextLabel
from spectra.core.scene import Scene
from .presentation_models import (
    LightingMode,
    PresentationContext,
    PresentationIntent,
    ResolvedPresentation,
    RevealMode,
    resolve_presentation,
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
    """Apply a renderer-neutral reveal without overriding scientific tracks.

    Cameras and lights are presentation controls and are not automatically
    revealed. A scientific track already owning the same
    ``(target_id, property_path)`` wins; the conflicting presentation effect is
    skipped rather than replacing physical/scientific animation.
    """
    if start_time < 0.0:
        raise ValueError("start_time cannot be negative")
    if item_duration <= 0.0:
        raise ValueError("item_duration must be positive")
    if stagger < 0.0:
        raise ValueError("stagger cannot be negative")

    occupied = {
        (track.target_id, track.property_path)
        for track in scene.timeline.tracks
    }
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

        candidate = (
            draw_track(primitive.id, start_time=item_start, end_time=item_end)
            if isinstance(primitive, Polyline)
            else fade_track(primitive.id, start_time=item_start, end_time=item_end)
        )
        key = (candidate.target_id, candidate.property_path)
        if key in occupied:
            continue
        occupied.add(key)
        tracks.append(candidate)
        end_time = max(end_time, item_end)

    if not tracks:
        return scene
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

    scientific = tuple(
        primitive
        for primitive in scene.primitives
        if not primitive.id.startswith("presentation.")
    )
    scientific_ids = {primitive.id for primitive in scientific}
    scientific_scene = replace(
        scene,
        primitives=scientific,
        active_camera_id=(
            scene.active_camera_id
            if scene.active_camera_id in scientific_ids
            else None
        ),
    )

    # Quantitative presentation is opt-in by semantic quantity role or explicit
    # scalar attribute name. This preserves scientific values and only adds a
    # renderer-neutral color attribute / current batched-color compatibility view.
    if context.quantity_role is not None or resolved.color_scale.scalar_attribute_name is not None:
        scientific_scene = colorize_scene(
            scientific_scene,
            resolved.color_scale,
            quantity_role=context.quantity_role,
        )
        scientific = scientific_scene.primitives

    if resolved.camera.mode.value == "fit_primary" and context.primary_primitive_id:
        target = scientific_scene.get(context.primary_primitive_id)
        camera_scene = replace(scientific_scene, primitives=(target,))
    else:
        camera_scene = scientific_scene

    camera = fit_camera_to_scene(
        camera_scene,
        padding=1.0 + resolved.camera.padding,
        camera_id="presentation.camera.primary",
        projection=resolved.camera.projection,
        aspect_ratio=resolved.camera.aspect_ratio,
        fov_y_radians=resolved.camera.fov_y_radians,
    )

    additions = [camera]
    if resolved.lighting.mode != LightingMode.UNLIT_DATA:
        additions.append(
            Light(
                id="presentation.light.key",
                light_type="directional",
                intensity=1.0,
            )
        )
        if resolved.lighting.mode in {
            LightingMode.SCIENTIFIC_STUDIO,
            LightingMode.RIM_EMPHASIS,
        }:
            additions.append(
                Light(
                    id="presentation.light.fill",
                    light_type="ambient",
                    intensity=0.35,
                )
            )
        if resolved.lighting.mode == LightingMode.RIM_EMPHASIS:
            additions.append(
                Light(
                    id="presentation.light.rim",
                    light_type="directional",
                    intensity=0.5,
                )
            )

    title = context.title or resolved.annotations.title
    subtitle = context.subtitle or resolved.annotations.subtitle
    if title:
        additions.append(
            TextLabel(
                id="presentation.title.primary",
                text=title,
                position=camera.transform.translation,
            )
        )
    if subtitle:
        additions.append(
            TextLabel(
                id="presentation.annotation.subtitle",
                text=subtitle,
                position=camera.transform.translation,
            )
        )
    if resolved.annotations.show_time and scene.timeline.duration > 0:
        additions.append(
            TextLabel(
                id="presentation.annotation.time",
                text="t = 0",
                position=camera.transform.translation,
            )
        )

    output = replace(
        scene,
        primitives=(*scientific, *additions),
        active_camera_id=camera.id,
    )
    if resolved.animation.reveal == RevealMode.STAGGERED:
        output = staggered_reveal(
            output,
            item_duration=resolved.animation.reveal_duration,
            stagger=resolved.animation.stagger,
        )
    return output


__all__ = [
    "ResolvedPresentation",
    "merge_timelines",
    "staggered_reveal",
    "compose_presentation",
]
