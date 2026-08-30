from __future__ import annotations

from spectra.compiler import compile_function1d
from spectra.core.primitives import Point, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.calculus.domain import tangent_at
from spectra.domains.mathematics.functions import Function1D


def compile_tangent_scene(
    function: Function1D,
    x: float,
    *,
    samples: int = 128,
    tangent_half_width: float | None = None,
) -> Scene:
    base_scene = compile_function1d(function, samples=samples, primitive_id="function")
    tangent = tangent_at(function, x)

    half_width = tangent_half_width
    if half_width is None:
        half_width = function.domain.length * 0.15
    if half_width <= 0:
        raise ValueError("tangent_half_width must be positive")

    left_x = max(function.domain.start, x - half_width)
    right_x = min(function.domain.end, x + half_width)
    if right_x <= left_x:
        raise ValueError("tangent segment has no visible extent")

    def tangent_y(sample_x: float) -> float:
        return tangent.y + tangent.slope * (sample_x - tangent.x)

    marker = Point(
        id="tangent.point",
        position=Vec3(tangent.x, tangent.y, 0.0),
        radius=0.06,
        color=Color(1.0, 0.45, 0.35, 1.0),
    )
    tangent_line = Polyline(
        id="tangent.line",
        points=(
            Vec3(left_x, tangent_y(left_x), 0.0),
            Vec3(right_x, tangent_y(right_x), 0.0),
        ),
        color=Color(1.0, 0.75, 0.25, 1.0),
    )
    return Scene(primitives=base_scene.primitives + (marker, tangent_line))
