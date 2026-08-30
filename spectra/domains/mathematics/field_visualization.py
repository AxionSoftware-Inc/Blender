from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color
from spectra.domains.mathematics.field_views import (
    TimeVectorFieldAnimation3D,
    VectorFieldView3D,
)


def compile_vector_field_view_scene(
    view: VectorFieldView3D,
    *,
    color: Color = Color(0.45, 0.75, 1.0, 1.0),
) -> Scene:
    origins = tuple(view.grid.points())
    vectors = tuple(view.field.evaluate(point) * view.vector_scale for point in origins)
    return Scene(
        primitives=(
            VectorGlyphSet(
                id=view.name,
                origins=origins,
                vectors=vectors,
                color=color,
            ),
        )
    )


def compile_time_vector_field_animation_scene(
    animation: TimeVectorFieldAnimation3D,
    *,
    color: Color = Color(0.45, 0.75, 1.0, 1.0),
) -> Scene:
    origins = tuple(animation.grid.points())
    duration = animation.duration
    engine_step = duration / (animation.temporal_samples - 1)

    keyframes = []
    for index in range(animation.temporal_samples):
        engine_time = index * engine_step
        physical_time = animation.start_time + engine_time
        vectors = tuple(
            animation.field.evaluate(point, physical_time) * animation.vector_scale
            for point in origins
        )
        keyframes.append(Keyframe(engine_time, vectors, "linear"))

    return Scene(
        primitives=(
            VectorGlyphSet(
                id=animation.name,
                origins=origins,
                vectors=keyframes[0].value,
                color=color,
            ),
        ),
        timeline=Timeline(
            duration=duration,
            tracks=(
                Track(
                    target_id=animation.name,
                    property_path="vectors",
                    keyframes=tuple(keyframes),
                ),
            ),
        ),
    )
