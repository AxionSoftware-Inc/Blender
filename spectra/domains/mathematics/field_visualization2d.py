from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Surface, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec2, Vec3
from spectra.domains.mathematics.field_views2d import (
    ScalarFieldHeightView2D,
    TimeScalarFieldHeightAnimation2D,
    TimeVectorFieldAnimation2D,
    VectorFieldView2D,
)


def _origins(x_values: tuple[float, ...], y_values: tuple[float, ...], plane_z: float) -> tuple[Vec3, ...]:
    return tuple(Vec3(x, y, plane_z) for y in y_values for x in x_values)


def compile_vector_field_view_2d_scene(
    view: VectorFieldView2D,
    *,
    color: Color = Color(0.38, 0.78, 1.0, 1.0),
) -> Scene:
    x_values = view.x.values()
    y_values = view.y.values()
    origins = _origins(x_values, y_values, view.plane_z)
    vectors = tuple(
        Vec3(
            (sample := view.field.evaluate(Vec2(origin.x, origin.y))).x * view.vector_scale,
            sample.y * view.vector_scale,
            0.0,
        )
        for origin in origins
    )
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


def compile_time_vector_field_animation_2d_scene(
    animation: TimeVectorFieldAnimation2D,
    *,
    color: Color = Color(0.38, 0.78, 1.0, 1.0),
) -> Scene:
    origins = _origins(animation.x.values(), animation.y.values(), animation.plane_z)
    engine_step = animation.duration / (animation.temporal_samples - 1)
    keyframes = []
    for index in range(animation.temporal_samples):
        engine_time = index * engine_step
        physical_time = animation.start_time + engine_time
        vectors = []
        for origin in origins:
            sample = animation.field.evaluate(Vec2(origin.x, origin.y), physical_time)
            vectors.append(Vec3(sample.x * animation.vector_scale, sample.y * animation.vector_scale, 0.0))
        keyframes.append(Keyframe(engine_time, tuple(vectors), "linear"))

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
            duration=animation.duration,
            tracks=(
                Track(
                    target_id=animation.name,
                    property_path="vectors",
                    keyframes=tuple(keyframes),
                ),
            ),
        ),
    )


def _triangles(x_count: int, y_count: int) -> tuple[tuple[int, int, int], ...]:
    result: list[tuple[int, int, int]] = []
    for y_index in range(y_count - 1):
        for x_index in range(x_count - 1):
            lower_left = y_index * x_count + x_index
            lower_right = lower_left + 1
            upper_left = lower_left + x_count
            upper_right = upper_left + 1
            result.append((lower_left, lower_right, upper_right))
            result.append((lower_left, upper_right, upper_left))
    return tuple(result)


def _height_vertices(
    field,
    x_values: tuple[float, ...],
    y_values: tuple[float, ...],
    *,
    height_scale: float,
    base_z: float,
    time: float | None = None,
) -> tuple[Vec3, ...]:
    vertices = []
    for y in y_values:
        for x in x_values:
            position = Vec2(x, y)
            value = field.evaluate(position) if time is None else field.evaluate(position, time)
            vertices.append(Vec3(x, y, base_z + value * height_scale))
    return tuple(vertices)


def compile_scalar_field_height_2d_scene(
    view: ScalarFieldHeightView2D,
    *,
    color: Color = Color(0.52, 0.72, 1.0, 0.92),
) -> Scene:
    x_values = view.x.values()
    y_values = view.y.values()
    return Scene(
        primitives=(
            Surface(
                id=view.name,
                vertices=_height_vertices(
                    view.field,
                    x_values,
                    y_values,
                    height_scale=view.height_scale,
                    base_z=view.base_z,
                ),
                triangles=_triangles(view.x.count, view.y.count),
                color=color,
            ),
        )
    )


def compile_time_scalar_field_height_2d_scene(
    animation: TimeScalarFieldHeightAnimation2D,
    *,
    color: Color = Color(0.52, 0.72, 1.0, 0.92),
) -> Scene:
    x_values = animation.x.values()
    y_values = animation.y.values()
    triangles = _triangles(animation.x.count, animation.y.count)
    engine_step = animation.duration / (animation.temporal_samples - 1)
    keyframes = []
    for index in range(animation.temporal_samples):
        engine_time = index * engine_step
        physical_time = animation.start_time + engine_time
        keyframes.append(
            Keyframe(
                engine_time,
                _height_vertices(
                    animation.field,
                    x_values,
                    y_values,
                    height_scale=animation.height_scale,
                    base_z=animation.base_z,
                    time=physical_time,
                ),
                "linear",
            )
        )

    return Scene(
        primitives=(
            Surface(
                id=animation.name,
                vertices=keyframes[0].value,
                triangles=triangles,
                color=color,
            ),
        ),
        timeline=Timeline(
            duration=animation.duration,
            tracks=(
                Track(
                    target_id=animation.name,
                    property_path="vertices",
                    keyframes=tuple(keyframes),
                ),
            ),
        ),
    )
