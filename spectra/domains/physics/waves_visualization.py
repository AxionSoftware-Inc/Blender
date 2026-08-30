from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.physics.waves import WaveAnimation1D, WaveLike1D, WaveProfile1D


def _sample_wave_points(wave: WaveLike1D, time: float, samples: int) -> tuple[Vec3, ...]:
    domain = wave.domain
    step = domain.length / (samples - 1)
    return tuple(
        Vec3(
            domain.start + index * step,
            wave.evaluate(domain.start + index * step, time),
            0.0,
        )
        for index in range(samples)
    )


def compile_wave_profile_scene(
    profile: WaveProfile1D,
    *,
    primitive_id: str | None = None,
    color: Color = Color(0.45, 0.8, 1.0, 1.0),
) -> Scene:
    return Scene(
        primitives=(
            Polyline(
                id=primitive_id or profile.name,
                points=_sample_wave_points(profile.wave, profile.time, profile.samples),
                width=0.025,
                color=color,
            ),
        )
    )


def compile_wave_animation_scene(
    animation: WaveAnimation1D,
    *,
    primitive_id: str | None = None,
    color: Color = Color(0.45, 0.8, 1.0, 1.0),
) -> Scene:
    """Compile physical wave time into an engine-owned Polyline.points track."""

    target_id = primitive_id or animation.name
    duration = animation.duration
    engine_step = duration / (animation.temporal_samples - 1)

    keyframes = []
    for index in range(animation.temporal_samples):
        engine_time = index * engine_step
        physical_time = animation.start_time + engine_time
        keyframes.append(
            Keyframe(
                engine_time,
                _sample_wave_points(
                    animation.wave,
                    physical_time,
                    animation.spatial_samples,
                ),
                "linear",
            )
        )

    initial_points = keyframes[0].value
    return Scene(
        primitives=(
            Polyline(
                id=target_id,
                points=initial_points,
                width=0.025,
                color=color,
            ),
        ),
        timeline=Timeline(
            duration=duration,
            tracks=(
                Track(
                    target_id=target_id,
                    property_path="points",
                    keyframes=tuple(keyframes),
                ),
            ),
        ),
    )
