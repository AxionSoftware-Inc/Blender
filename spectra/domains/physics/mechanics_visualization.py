from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track, draw_track
from spectra.core.primitives import Point, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.physics.mechanics import Trajectory


def compile_trajectory_scene(
    trajectory: Trajectory,
    *,
    primitive_prefix: str = "trajectory",
) -> Scene:
    if len(trajectory.positions) < 2:
        raise ValueError("trajectory visualization requires at least two positions")

    path = Polyline(
        id=f"{primitive_prefix}.path",
        points=trajectory.positions,
        color=Color(0.55, 0.9, 1.0, 1.0),
    )
    start = Point(
        id=f"{primitive_prefix}.start",
        position=trajectory.positions[0],
        radius=0.06,
        color=Color(0.3, 1.0, 0.55, 1.0),
    )
    end = Point(
        id=f"{primitive_prefix}.end",
        position=trajectory.positions[-1],
        radius=0.06,
        color=Color(1.0, 0.45, 0.35, 1.0),
    )
    return Scene(primitives=(path, start, end))


def compile_animated_trajectory_scene(
    trajectory: Trajectory,
    *,
    primitive_prefix: str = "trajectory",
    particle_radius: float = 0.07,
    draw_path: bool = True,
) -> Scene:
    """Compile physical trajectory time directly into an engine-owned timeline."""
    if len(trajectory.positions) < 2:
        raise ValueError("animated trajectory requires at least two positions")
    if particle_radius <= 0.0:
        raise ValueError("particle_radius must be positive")

    start_time = trajectory.times[0]
    duration = trajectory.times[-1] - start_time
    if duration <= 0.0:
        raise ValueError("animated trajectory requires positive duration")

    path_id = f"{primitive_prefix}.path"
    particle_id = f"{primitive_prefix}.particle"
    path = Polyline(
        id=path_id,
        points=trajectory.positions,
        color=Color(0.55, 0.9, 1.0, 1.0),
    )
    particle = Point(
        id=particle_id,
        position=trajectory.positions[0],
        radius=particle_radius,
        color=Color(1.0, 0.8, 0.25, 1.0),
    )

    position_keyframes = tuple(
        Keyframe(
            time - start_time,
            position,
            "linear",
        )
        for time, position in zip(trajectory.times, trajectory.positions, strict=True)
    )
    tracks: list[Track[object]] = [
        Track(
            target_id=particle_id,
            property_path="position",
            keyframes=position_keyframes,
        )
    ]
    if draw_path:
        tracks.append(
            draw_track(
                path_id,
                start_time=0.0,
                end_time=duration,
                interpolation="linear",
            )
        )

    return Scene(
        primitives=(path, particle),
        timeline=Timeline(duration=duration, tracks=tuple(tracks)),
    )
