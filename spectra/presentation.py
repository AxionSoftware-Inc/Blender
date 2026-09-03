from __future__ import annotations

from dataclasses import replace

from spectra.color_scales import (
    ResolvedColorScale,
    colorize_scene,
    resolve_scene_color_scale,
    sample_palette,
)
from spectra.core.animation import Timeline, Track, draw_track, fade_track
from spectra.core.bounds import Bounds3D, scene_local_bounds
from spectra.core.framing import fit_camera_to_scene
from spectra.core.primitives import Camera, Group, Light, Polyline, TextLabel
from spectra.core.scene import Scene
from spectra.core.transforms import Transform3D
from spectra.core.types import Color, Vec3
from .presentation_models import (
    LegendPolicy,
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
            draw_track(
                primitive.id,
                start_time=item_start,
                end_time=item_end,
                owner="presentation",
            )
            if isinstance(primitive, Polyline)
            else fade_track(
                primitive.id,
                start_time=item_start,
                end_time=item_end,
                owner="presentation",
            )
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


def _scientific_timeline(scene: Scene) -> Timeline:
    """Drop presentation-owned tracks while retaining scientific duration."""
    tracks = tuple(
        track
        for track in scene.timeline.tracks
        if track.owner != "presentation"
        and not track.target_id.startswith("presentation.")
    )
    return Timeline(duration=scene.timeline.duration, tracks=tracks)


def _legend_transform(camera: Camera, bounds: Bounds3D) -> tuple[Transform3D, float]:
    """Place a small camera-facing legend near the right side of scientific data."""
    radius = max(bounds.bounding_sphere_radius, 1e-3)
    right = camera.transform.rotation.rotate(Vec3(1.0, 0.0, 0.0))
    up = camera.transform.rotation.rotate(Vec3(0.0, 1.0, 0.0))
    toward_camera = camera.transform.rotation.rotate(Vec3(0.0, 0.0, 1.0))
    anchor = (
        bounds.center
        + right * (radius * 0.72)
        + up * (radius * 0.18)
        + toward_camera * (radius * 0.08)
    )
    return Transform3D(
        translation=anchor,
        rotation=camera.transform.rotation,
    ), radius


def _format_scale_value(value: float) -> str:
    return f"{value:.4g}"


def _quantitative_legend(
    scale: ResolvedColorScale,
    camera: Camera,
    bounds: Bounds3D,
    policy: LegendPolicy,
    *,
    fallback_role: str | None,
) -> tuple[object, ...]:
    transform, radius = _legend_transform(camera, bounds)
    height = max(radius * 0.60, 0.25)
    width = max(radius * 0.16, 0.08)
    samples = 5 if policy.compact else 8
    segment_height = height / samples
    line_width = max(width * 0.60, 0.01)

    primitives: list[object] = []
    child_ids: list[str] = []
    for index in range(samples):
        position = index / max(samples - 1, 1)
        y = -height * 0.5 + (index + 0.5) * segment_height
        primitive_id = f"presentation.legend.scale.{index:02d}"
        child_ids.append(primitive_id)
        primitives.append(
            Polyline(
                id=primitive_id,
                points=(Vec3(-width * 0.5, y, 0.0), Vec3(width * 0.5, y, 0.0)),
                width=line_width,
                color=sample_palette(scale.palette, position),
                transform=transform,
            )
        )

    quantity_label = scale.quantity_id or fallback_role or "value"
    if policy.show_units and scale.unit is not None:
        quantity_label = f"{quantity_label} [{scale.unit.symbol}]"
    title_id = "presentation.legend.label.quantity"
    child_ids.append(title_id)
    primitives.append(
        TextLabel(
            id=title_id,
            text=quantity_label,
            position=Vec3(-width * 0.5, height * 0.68, 0.0),
            size=max(radius * 0.07, 0.04),
            color=Color(1.0, 1.0, 1.0, 1.0),
            transform=transform,
        )
    )

    if policy.show_min_max:
        minimum_id = "presentation.legend.label.minimum"
        maximum_id = "presentation.legend.label.maximum"
        child_ids.extend((minimum_id, maximum_id))
        label_size = max(radius * 0.06, 0.035)
        primitives.extend(
            (
                TextLabel(
                    id=minimum_id,
                    text=_format_scale_value(scale.minimum),
                    position=Vec3(width * 0.72, -height * 0.5, 0.0),
                    size=label_size,
                    color=Color(1.0, 1.0, 1.0, 1.0),
                    transform=transform,
                ),
                TextLabel(
                    id=maximum_id,
                    text=_format_scale_value(scale.maximum),
                    position=Vec3(width * 0.72, height * 0.5, 0.0),
                    size=label_size,
                    color=Color(1.0, 1.0, 1.0, 1.0),
                    transform=transform,
                ),
            )
        )

    primitives.append(
        Group(
            id="presentation.legend.quantitative",
            children=tuple(child_ids),
        )
    )
    return tuple(primitives)


def _analysis_axes(bounds: Bounds3D) -> tuple[object, ...]:
    """Create a compact Scene-local XYZ triad without affecting camera framing."""
    size = bounds.size
    length = max(max(abs(size.x), abs(size.y), abs(size.z)) * 0.22, 0.25)
    origin = bounds.minimum
    width = max(length * 0.025, 0.006)
    label_size = max(length * 0.14, 0.04)
    definitions = (
        ("x", Vec3(length, 0.0, 0.0), Color(1.0, 0.25, 0.25, 1.0)),
        ("y", Vec3(0.0, length, 0.0), Color(0.25, 1.0, 0.35, 1.0)),
        ("z", Vec3(0.0, 0.0, length), Color(0.30, 0.55, 1.0, 1.0)),
    )
    primitives: list[object] = []
    child_ids: list[str] = []
    for axis, vector, color in definitions:
        line_id = f"presentation.axes.{axis}"
        label_id = f"presentation.axes.{axis}.label"
        child_ids.extend((line_id, label_id))
        primitives.extend(
            (
                Polyline(
                    id=line_id,
                    points=(origin, origin + vector),
                    width=width,
                    color=color,
                ),
                TextLabel(
                    id=label_id,
                    text=axis.upper(),
                    position=origin + vector * 1.08,
                    size=label_size,
                    color=color,
                ),
            )
        )
    primitives.append(
        Group(
            id="presentation.axes.world",
            children=tuple(child_ids),
        )
    )
    return tuple(primitives)


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
        timeline=_scientific_timeline(scene),
        active_camera_id=(
            scene.active_camera_id
            if scene.active_camera_id in scientific_ids
            else None
        ),
    )

    quantitative_scale = None
    if context.quantity_role is not None or resolved.color_scale.scalar_attribute_name is not None:
        quantitative_scale = resolve_scene_color_scale(
            scientific_scene,
            resolved.color_scale,
            quantity_role=context.quantity_role,
        )
        scientific_scene = colorize_scene(
            scientific_scene,
            resolved.color_scale,
            quantity_role=context.quantity_role,
        )
        scientific = scientific_scene.primitives

    scientific_bounds = scene_local_bounds(scientific_scene)
    if resolved.camera.mode.value == "fit_primary" and context.primary_primitive_id:
        target = scientific_scene.get(context.primary_primitive_id)
        camera_scene = replace(
            scientific_scene,
            primitives=(target,),
            timeline=Timeline(),
            active_camera_id=None,
        )
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

    additions: list[object] = [camera]
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

    if resolved.axes.visible:
        additions.extend(_analysis_axes(scientific_bounds))

    if resolved.legend.visible and quantitative_scale is not None:
        additions.extend(
            _quantitative_legend(
                quantitative_scale,
                camera,
                scientific_bounds,
                resolved.legend,
                fallback_role=(
                    context.quantity_role
                    or resolved.color_scale.scalar_attribute_name
                ),
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
    if resolved.annotations.show_time and scientific_scene.timeline.duration > 0:
        additions.append(
            TextLabel(
                id="presentation.annotation.time",
                text="t = 0",
                position=camera.transform.translation,
            )
        )

    output = replace(
        scientific_scene,
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
