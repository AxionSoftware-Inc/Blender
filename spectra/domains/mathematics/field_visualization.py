from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Surface, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.mathematics.field_views import (
    ScalarFieldSurfaceView2D,
    TimeScalarFieldSurfaceAnimation2D,
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


def _surface_triangles(x_count: int, y_count: int) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for y_index in range(y_count - 1):
        for x_index in range(x_count - 1):
            lower_left = y_index * x_count + x_index
            lower_right = lower_left + 1
            upper_left = lower_left + x_count
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))
    return tuple(triangles)


def _sample_scalar_surface_vertices(
    field,
    x_values: tuple[float, ...],
    y_values: tuple[float, ...],
    *,
    plane_z: float,
    height_scale: float,
    time: float | None = None,
) -> tuple[Vec3, ...]:
    vertices = []
    for y in y_values:
        for x in x_values:
            sample_position = Vec3(x, y, plane_z)
            if time is None:
                value = field.evaluate(sample_position)
            else:
                value = field.evaluate(sample_position, time)
            vertices.append(Vec3(x, y, plane_z + value * height_scale))
    return tuple(vertices)


def compile_scalar_field_surface_scene(
    view: ScalarFieldSurfaceView2D,
    *,
    color: Color = Color(0.55, 0.72, 1.0, 0.92),
) -> Scene:
    x_values = view.x.values()
    y_values = view.y.values()
    vertices = _sample_scalar_surface_vertices(
        view.field,
        x_values,
        y_values,
        plane_z=view.plane_z,
        height_scale=view.height_scale,
    )
    return Scene(
        primitives=(
            Surface(
                id=view.name,
                vertices=vertices,
                triangles=_surface_triangles(view.x.count, view.y.count),
                color=color,
            ),
        )
    )


def compile_time_scalar_field_surface_animation_scene(
    animation: TimeScalarFieldSurfaceAnimation2D,
    *,
    color: Color = Color(0.55, 0.72, 1.0, 0.92),
) -> Scene:
    x_values = animation.x.values()
    y_values = animation.y.values()
    triangles = _surface_triangles(animation.x.count, animation.y.count)
    duration = animation.duration
    engine_step = duration / (animation.temporal_samples - 1)

    keyframes = []
    for index in range(animation.temporal_samples):
        engine_time = index * engine_step
        physical_time = animation.start_time + engine_time
        vertices = _sample_scalar_surface_vertices(
            animation.field,
            x_values,
            y_values,
            plane_z=animation.plane_z,
            height_scale=animation.height_scale,
            time=physical_time,
        )
        keyframes.append(Keyframe(engine_time, vertices, "linear"))

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
            duration=duration,
            tracks=(
                Track(
                    target_id=animation.name,
                    property_path="vertices",
                    keyframes=tuple(keyframes),
                ),
            ),
        ),
    )
