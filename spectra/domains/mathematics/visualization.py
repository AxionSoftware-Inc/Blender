from __future__ import annotations

from spectra.core.primitives import VectorGlyph
from spectra.core.scene import Scene
from spectra.core.types import Color
from spectra.domains.mathematics.fields import RegularGrid3D, VectorField3D


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
