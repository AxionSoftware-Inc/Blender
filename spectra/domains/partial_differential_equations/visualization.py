from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.partial_differential_equations.domain import ScalarPDESolution1D


def _profile_points(solution: ScalarPDESolution1D, state: tuple[float, ...]) -> tuple[Vec3, ...]:
    return tuple(
        Vec3(x, value, 0.0)
        for x, value in zip(solution.grid.coordinates, state, strict=True)
    )


def compile_scalar_pde_solution_scene(
    solution: ScalarPDESolution1D,
    *,
    color: Color = Color(0.45, 0.75, 1.0, 1.0),
    width: float = 0.02,
) -> Scene:
    """Visualize a PDE solution as an engine-owned animated profile curve."""

    primitive_id = f"{solution.name}.profile"
    start_time = solution.times[0]
    keyframes = tuple(
        Keyframe(
            time - start_time,
            _profile_points(solution, state),
            "linear",
        )
        for time, state in zip(solution.times, solution.states, strict=True)
    )
    initial_points = keyframes[0].value

    timeline = Timeline()
    if solution.duration > 0.0:
        timeline = Timeline(
            duration=solution.duration,
            tracks=(
                Track(
                    target_id=primitive_id,
                    property_path="points",
                    keyframes=keyframes,
                ),
            ),
        )

    return Scene(
        primitives=(
            Polyline(
                id=primitive_id,
                points=initial_points,
                color=color,
                width=width,
            ),
        ),
        timeline=timeline,
    )
