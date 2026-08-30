from __future__ import annotations

from collections.abc import Callable

from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3


def sample_function(
    fn: Callable[[float], float],
    *,
    x_min: float,
    x_max: float,
    samples: int = 128,
    primitive_id: str = "function",
) -> Scene:
    """First architecture proof: scientific function -> renderer-independent Scene."""
    if samples < 2:
        raise ValueError("samples must be >= 2")
    if x_max <= x_min:
        raise ValueError("x_max must be greater than x_min")

    step = (x_max - x_min) / (samples - 1)
    points = tuple(
        Vec3(x_min + step * index, float(fn(x_min + step * index)), 0.0)
        for index in range(samples)
    )
    curve = Polyline(
        id=primitive_id,
        points=points,
        color=Color(0.95, 0.95, 1.0, 1.0),
    )
    return Scene(primitives=(curve,))
