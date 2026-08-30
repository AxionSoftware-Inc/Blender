from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Surface
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.partial_differential_equations.domain2d import ScalarPDESolution2D


def _surface_triangles(samples_x: int, samples_y: int) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for y_index in range(samples_y - 1):
        for x_index in range(samples_x - 1):
            lower_left = y_index * samples_x + x_index
            lower_right = lower_left + 1
            upper_left = lower_left + samples_x
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))
    return tuple(triangles)


def _vertices(solution: ScalarPDESolution2D, state: tuple[float, ...]) -> tuple[Vec3, ...]:
    return tuple(
        Vec3(x, y, value)
        for (x, y), value in zip(solution.grid.coordinates, state, strict=True)
    )


def compile_scalar_pde_solution_2d_scene(
    solution: ScalarPDESolution2D,
    *,
    primitive_id: str | None = None,
    color: Color = Color(0.45, 0.7, 1.0, 0.92),
) -> Scene:
    """Compile a scalar 2D PDE solution into one topology-stable animated Surface."""

    surface_id = primitive_id or f"{solution.name}.surface"
    start_time = solution.times[0]
    duration = solution.duration
    keyframes = tuple(
        Keyframe(
            time - start_time,
            _vertices(solution, state),
            "linear",
        )
        for time, state in zip(solution.times, solution.states, strict=True)
    )
    initial_vertices = keyframes[0].value
    surface = Surface(
        id=surface_id,
        vertices=initial_vertices,
        triangles=_surface_triangles(solution.grid.x.count, solution.grid.y.count),
        color=color,
    )
    timeline = Timeline(
        duration=duration,
        tracks=(
            Track(
                target_id=surface_id,
                property_path="vertices",
                keyframes=keyframes,
            ),
        ),
    )
    return Scene(primitives=(surface,), timeline=timeline)
