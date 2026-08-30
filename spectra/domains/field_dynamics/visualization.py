from __future__ import annotations

from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color
from spectra.domains.field_dynamics.domain import CurveSolution3D


def compile_curve_solution_scene(
    solution: CurveSolution3D,
    *,
    primitive_id: str = "field_curve",
    color: Color = Color(0.95, 0.72, 0.25, 1.0),
    width: float = 0.02,
) -> Scene:
    return Scene(
        primitives=(
            Polyline(
                id=primitive_id,
                points=solution.positions,
                width=width,
                color=color,
            ),
        )
    )
