from __future__ import annotations

from spectra.core.primitives import Point, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color
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
