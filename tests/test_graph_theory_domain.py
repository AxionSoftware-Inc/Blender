from __future__ import annotations

from spectra.core.types import Vec2
from spectra.domains import DomainRegistry
from spectra.domains.graph_theory import (
    Edge,
    Graph,
    GraphLayout2D,
    GraphTheoryDomain,
    NodePlacement2D,
)


def test_graph_theory_is_independent_and_visualizable() -> None:
    registry = DomainRegistry()
    registry.add_domain(GraphTheoryDomain())

    graph = Graph(
        nodes=("A", "B", "C", "D"),
        edges=(
            Edge("A", "B"),
            Edge("B", "C"),
            Edge("A", "D"),
            Edge("D", "C"),
        ),
    )
    shortest_path = registry.require("graph_theory.shortest_path_unweighted")
    path = shortest_path(graph, "A", "C")
    assert path in (("A", "B", "C"), ("A", "D", "C"))

    layout = GraphLayout2D(
        graph=graph,
        placements=(
            NodePlacement2D("A", Vec2(-1.0, 0.0)),
            NodePlacement2D("B", Vec2(0.0, 1.0)),
            NodePlacement2D("C", Vec2(1.0, 0.0)),
            NodePlacement2D("D", Vec2(0.0, -1.0)),
        ),
        name="diamond",
    )
    scene = registry.compile_scene(layout)

    assert scene.get("diamond.node.A") is not None
    assert scene.get("diamond.edge.0") is not None
    assert len(scene.primitives) == len(graph.edges) + 2 * len(graph.nodes)
