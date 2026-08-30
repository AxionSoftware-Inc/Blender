from __future__ import annotations

from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.differential_geometry.geodesics import GeodesicView3D


def compile_geodesic_view_scene(
    view: GeodesicView3D,
    *,
    color: Color = Color(1.0, 0.72, 0.32, 1.0),
) -> Scene:
    def component(position: tuple[float, ...], axis: int | None) -> float:
        return 0.0 if axis is None else position[axis]

    points = tuple(
        Vec3(
            component(position, view.axes[0]),
            component(position, view.axes[1]),
            component(position, view.axes[2]),
        )
        for position in view.solution.positions
    )
    return Scene(
        primitives=(
            Polyline(
                id=view.name,
                points=points,
                color=color,
            ),
        )
    )
