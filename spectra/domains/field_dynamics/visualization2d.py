from __future__ import annotations

from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.field_dynamics.domain2d import CurveSolution2D


def compile_curve_solution_2d_scene(
    solution: CurveSolution2D,
    *,
    primitive_id: str = "field_curve2d",
    color: Color = Color(0.95, 0.72, 0.25, 1.0),
    width: float = 0.02,
) -> Scene:
    return Scene(
        primitives=(
            Polyline(
                id=primitive_id,
                points=tuple(Vec3(position.x, position.y, 0.0) for position in solution.positions),
                width=width,
                color=color,
            ),
        )
    )
