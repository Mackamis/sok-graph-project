from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from datetime import date

AttrValue = int | str | float | date


class Node:

    def __init__(
        self,
        node_id: Hashable,
        attributes: Mapping[str, AttrValue] | None = None,
    ) -> None:
        raise NotImplementedError

    @property
    def id(self) -> Hashable:
        raise NotImplementedError

    @property
    def attributes(self) -> Mapping[str, AttrValue]: # Return a read-only view of the node's attributes
        raise NotImplementedError

    def set_attribute(self, key: str, value: AttrValue) -> None:
        raise NotImplementedError

    def remove_attribute(self, key: str) -> None:
        raise NotImplementedError


class Edge:

    def __init__(
        self,
        edge_id: Hashable,
        source: Hashable,
        target: Hashable,
        attributes: Mapping[str, AttrValue] | None = None,
    ) -> None:
        raise NotImplementedError

    @property
    def id(self) -> Hashable:
        raise NotImplementedError

    @property
    def source(self) -> Hashable:
        raise NotImplementedError

    @property
    def target(self) -> Hashable:
        raise NotImplementedError

    @property
    def attributes(self) -> Mapping[str, AttrValue]: # Return a read-only view of the edge's attributes
        raise NotImplementedError

    def set_attribute(self, key: str, value: AttrValue) -> None: # Set or update an attribute after validating its exact runtime type
        raise NotImplementedError

    def remove_attribute(self, key: str) -> None:
        raise NotImplementedError


class Graph:

    def __init__(self, directed: bool = True) -> None:    
        raise NotImplementedError

    @property
    def directed(self) -> bool:
        raise NotImplementedError

    @property
    def nodes(self) -> Mapping[Hashable, Node]:
        raise NotImplementedError

    @property
    def edges(self) -> Mapping[Hashable, Edge]:
        raise NotImplementedError

    def add_node(self, node: Node) -> None:
        raise NotImplementedError

    def add_edge(self, edge: Edge) -> None:
        raise NotImplementedError

    def remove_node(self, node_id: Hashable) -> None:
        raise NotImplementedError

    def remove_edge(self, edge_id: Hashable) -> None:
        raise NotImplementedError

    def get_node(self, node_id: Hashable) -> Node:
        raise NotImplementedError

    def get_edge(self, edge_id: Hashable) -> Edge:
        raise NotImplementedError

    def edges_for(self, node_id: Hashable) -> list[Edge]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def neighbors(self, node_id: Hashable) -> list[Node]:
        """Return every node adjacent to node_id, each exactly once.

        Incoming and outgoing edges both count. A node is never its own
        neighbor, so self-loops are ignored. Raises NotFoundError if node_id
        does not exist.
        """

    def outgoing_neighbors(self, node_id: Hashable) -> list[Node]:
        """Return every node reachable from node_id over one outgoing edge, each once.

        In an undirected graph every edge can be followed in both directions,
        so this equals neighbors(). Self-loops are ignored. Raises
        NotFoundError if node_id does not exist.
        """

    def connected_components(self) -> list[set[Hashable]]:
        """Return the weakly connected components as sets of node ids.

        Edge direction is ignored: two nodes share a component if a path
        joins them when every edge is treated as undirected. Isolated nodes
        form singleton components. An empty graph has no components.
        """

    def is_connected(self) -> bool:
        """Return True if the graph has exactly one weakly connected component.

        Edge direction is ignored (see connected_components). An empty graph
        is not connected.
        """

    def has_cycle(self) -> bool:
        """Return True if the graph contains at least one cycle.

        Directed graph: a cycle that follows edge direction, such as
        A->B->A or a self-loop. Undirected graph: a closed path that never
        reuses an edge; a self-loop counts. Directed and undirected graphs
        need different detection algorithms.
        """