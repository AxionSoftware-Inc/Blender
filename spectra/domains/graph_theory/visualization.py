from __future__ import annotations

from spectra.core.primitives import Point, Polyline, TextLabel, VectorGlyph
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.graph_theory.domain import GraphLayout2D


def _to_vec3(x: float, y: float) -> Vec3:
    return Vec3(x, y, 0.0)


def compile_graph_layout_scene(layout: GraphLayout2D) -> Scene:
    primitives = []

    for index, edge in enumerate(layout.graph.edges):
        start2 = layout.position_for(edge.source)
        end2 = layout.position_for(edge.target)
        start = _to_vec3(start2.x, start2.y)
        end = _to_vec3(end2.x, end2.y)
        if layout.graph.directed:
            primitives.append(
                VectorGlyph(
                    id=f"{layout.name}.edge.{index}",
                    origin=start,
                    vector=end - start,
                    color=Color(0.65, 0.75, 1.0, 1.0),
                )
            )
        else:
            primitives.append(
                Polyline(
                    id=f"{layout.name}.edge.{index}",
                    points=(start, end),
                    width=0.025,
                    color=Color(0.65, 0.75, 1.0, 1.0),
                )
            )

    for node in layout.graph.nodes:
        position2 = layout.position_for(node)
        position = _to_vec3(position2.x, position2.y)
        primitives.append(
            Point(
                id=f"{layout.name}.node.{node}",
                position=position,
                radius=0.07,
                color=Color(0.35, 0.9, 0.7, 1.0),
            )
        )
        primitives.append(
            TextLabel(
                id=f"{layout.name}.label.{node}",
                text=node,
                position=position,
                size=0.65,
            )
        )

    return Scene(primitives=tuple(primitives))
