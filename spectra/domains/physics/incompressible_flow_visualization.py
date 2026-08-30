from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.physics.incompressible_flow import IncompressibleFlowSolution2D


def compile_incompressible_flow_scene(
    solution: IncompressibleFlowSolution2D,
    *,
    vector_scale: float = 1.0,
    color: Color = Color(0.25, 0.72, 1.0, 1.0),
) -> Scene:
    if vector_scale <= 0.0:
        raise ValueError("flow visualization vector_scale must be positive")

    origins = tuple(Vec3(x, y, 0.0) for x, y in solution.grid.coordinates)
    start_time = solution.states[0].time
    keyframes = tuple(
        Keyframe(
            state.time - start_time,
            tuple(
                Vec3(vector.x * vector_scale, vector.y * vector_scale, 0.0)
                for vector in state.velocity
            ),
            "linear",
        )
        for state in solution.states
    )
    primitive_id = f"{solution.name}.velocity"
    return Scene(
        primitives=(
            VectorGlyphSet(
                id=primitive_id,
                origins=origins,
                vectors=keyframes[0].value,
                color=color,
            ),
        ),
        timeline=Timeline(
            duration=solution.duration,
            tracks=(
                Track(
                    target_id=primitive_id,
                    property_path="vectors",
                    keyframes=keyframes,
                ),
            ),
        ),
    )
