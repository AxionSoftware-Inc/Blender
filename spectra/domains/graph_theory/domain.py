from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from spectra.core.types import Vec2
from spectra.domains.registry import DomainRegistry


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class Graph:
    nodes: tuple[str, ...]
    edges: tuple[Edge, ...]
    directed: bool = False

    def __post_init__(self) -> None:
        if len(self.nodes) != len(set(self.nodes)):
            raise ValueError("graph node ids must be unique")
        node_set = set(self.nodes)
        for edge in self.edges:
            if edge.source not in node_set or edge.target not in node_set:
                raise ValueError("graph edge references an unknown node")


@dataclass(frozen=True, slots=True)
class NodePlacement2D:
    node: str
    position: Vec2


@dataclass(frozen=True, slots=True)
class GraphLayout2D:
    graph: Graph
    placements: tuple[NodePlacement2D, ...]
    name: str = "graph"

    def __post_init__(self) -> None:
        placement_nodes = [placement.node for placement in self.placements]
        if len(placement_nodes) != len(set(placement_nodes)):
            raise ValueError("graph layout contains duplicate node placements")
        if set(placement_nodes) != set(self.graph.nodes):
            raise ValueError("graph layout must place every graph node exactly once")

    def position_for(self, node: str) -> Vec2:
        for placement in self.placements:
            if placement.node == node:
                return placement.position
        raise KeyError(node)


def neighbors(graph: Graph, node: str) -> tuple[str, ...]:
    if node not in graph.nodes:
        raise KeyError(node)
    result: list[str] = []
    for edge in graph.edges:
        if edge.source == node:
            result.append(edge.target)
        if not graph.directed and edge.target == node:
            result.append(edge.source)
    return tuple(result)


def shortest_path_unweighted(graph: Graph, start: str, goal: str) -> tuple[str, ...]:
    if start not in graph.nodes or goal not in graph.nodes:
        raise KeyError("start and goal must be graph nodes")
    if start == goal:
        return (start,)

    queue = deque([start])
    previous: dict[str, str | None] = {start: None}
    while queue:
        current = queue.popleft()
        for neighbor in neighbors(graph, current):
            if neighbor in previous:
                continue
            previous[neighbor] = current
            if neighbor == goal:
                path = [goal]
                cursor: str | None = goal
                while cursor is not None and previous[cursor] is not None:
                    cursor = previous[cursor]
                    if cursor is not None:
                        path.append(cursor)
                return tuple(reversed(path))
            queue.append(neighbor)
    return ()


class GraphTheoryDomain:
    name = "graph_theory"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.graph_theory.visualization import compile_graph_layout_scene

        registry.register_semantic_type("graph_theory.edge", Edge)
        registry.register_semantic_type("graph_theory.graph", Graph)
        registry.register_semantic_type("graph_theory.layout2d", GraphLayout2D)

        registry.provide("graph_theory.graph", Graph)
        registry.provide("graph_theory.neighbors", neighbors)
        registry.provide("graph_theory.shortest_path_unweighted", shortest_path_unweighted)

        registry.register_visualization(GraphLayout2D, compile_graph_layout_scene)
