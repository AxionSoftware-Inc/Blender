from __future__ import annotations

from spectra.core.primitives import Polyline, Surface, VectorGlyph
from spectra.core.scene import Scene
from spectra.core.types import Color
from spectra.domains.mathematics.fields import RegularGrid3D, VectorField3D
from spectra.domains.mathematics.parametric import ParametricCurve3D, ParametricSurface3D


def compile_parametric_curve_scene(
    curve: ParametricCurve3D,
    *,
    samples: int = 128,
    parameters: dict[str, float] | None = None,
) -> Scene:
    if samples < 2:
        raise ValueError("samples must be >= 2")
    parameters = parameters or {}
    step = curve.domain.length / (samples - 1)
    points = tuple(
        curve.evaluate(curve.domain.start + step * index, **parameters)
        for index in range(samples)
    )
    return Scene(
        primitives=(
            Polyline(
                id=curve.name,
                points=points,
                color=Color(0.65, 0.9, 1.0, 1.0),
            ),
        )
    )


def compile_parametric_surface_scene(
    surface: ParametricSurface3D,
    *,
    samples_u: int = 48,
    samples_v: int = 48,
    parameters: dict[str, float] | None = None,
) -> Scene:
    if samples_u < 2 or samples_v < 2:
        raise ValueError("samples_u and samples_v must be >= 2")
    parameters = parameters or {}
    u_domain = surface.domain.x
    v_domain = surface.domain.y
    u_step = u_domain.length / (samples_u - 1)
    v_step = v_domain.length / (samples_v - 1)

    vertices = []
    for v_index in range(samples_v):
        v = v_domain.start + v_step * v_index
        for u_index in range(samples_u):
            u = u_domain.start + u_step * u_index
            vertices.append(surface.evaluate(u, v, **parameters))

    triangles = []
    for v_index in range(samples_v - 1):
        for u_index in range(samples_u - 1):
            lower_left = v_index * samples_u + u_index
            lower_right = lower_left + 1
            upper_left = lower_left + samples_u
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))

    return Scene(
        primitives=(
            Surface(
                id=surface.name,
                vertices=tuple(vertices),
                triangles=tuple(triangles),
                color=Color(0.6, 0.78, 1.0, 0.92),
            ),
        )
    )


def compile_vector_field_scene(
    field: VectorField3D,
    grid: RegularGrid3D,
    *,
    vector_scale: float = 1.0,
    primitive_prefix: str = "vector_field",
    color: Color = Color(0.45, 0.75, 1.0, 1.0),
) -> Scene:
    """Compile a mathematical vector field into renderer-independent glyphs."""
    if vector_scale <= 0.0:
        raise ValueError("vector_scale must be positive")

    primitives = []
    for index, position in enumerate(grid.points()):
        primitives.append(
            VectorGlyph(
                id=f"{primitive_prefix}.{index}",
                origin=position,
                vector=field.evaluate(position) * vector_scale,
                color=color,
            )
        )
    return Scene(primitives=tuple(primitives))
