from __future__ import annotations

from collections.abc import Callable

from spectra.core.primitives import Polyline, Surface
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.mathematics.functions import Function2D, RealFunction1D


def compile_function1d(
    function: RealFunction1D,
    *,
    samples: int = 128,
    primitive_id: str = "function",
    parameters: dict[str, float] | None = None,
) -> Scene:
    """Compile any real 1D function contract into a renderer-independent Scene."""
    if samples < 2:
        raise ValueError("samples must be >= 2")

    parameters = parameters or {}
    start = function.domain.start
    step = function.domain.length / (samples - 1)
    points = tuple(
        Vec3(
            x := start + step * index,
            function.evaluate(x, **parameters),
            0.0,
        )
        for index in range(samples)
    )
    curve = Polyline(
        id=primitive_id,
        points=points,
        color=Color(0.95, 0.95, 1.0, 1.0),
    )
    return Scene(primitives=(curve,))


def compile_function2d(
    function: Function2D,
    *,
    samples_x: int = 48,
    samples_y: int = 48,
    primitive_id: str = "surface",
    parameters: dict[str, float] | None = None,
) -> Scene:
    """Compile z=f(x,y) over a rectangular domain into an indexed Surface."""
    if samples_x < 2 or samples_y < 2:
        raise ValueError("samples_x and samples_y must be >= 2")

    parameters = parameters or {}
    x_domain = function.domain.x
    y_domain = function.domain.y
    x_step = x_domain.length / (samples_x - 1)
    y_step = y_domain.length / (samples_y - 1)

    vertices = []
    for y_index in range(samples_y):
        y = y_domain.start + y_step * y_index
        for x_index in range(samples_x):
            x = x_domain.start + x_step * x_index
            vertices.append(Vec3(x, y, function.evaluate(x, y, **parameters)))

    triangles = []
    for y_index in range(samples_y - 1):
        for x_index in range(samples_x - 1):
            lower_left = y_index * samples_x + x_index
            lower_right = lower_left + 1
            upper_left = lower_left + samples_x
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))

    surface = Surface(
        id=primitive_id,
        vertices=tuple(vertices),
        triangles=tuple(triangles),
        color=Color(0.55, 0.75, 1.0, 0.92),
    )
    return Scene(primitives=(surface,))


def sample_function(
    fn: Callable[[float], float],
    *,
    x_min: float,
    x_max: float,
    samples: int = 128,
    primitive_id: str = "function",
) -> Scene:
    """Compatibility helper for raw callables during early migration.

    New domain code should prefer a semantic RealFunction1D implementation so
    scientific meaning exists before visualization compilation.
    """
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
