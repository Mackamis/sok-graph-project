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
        raise NotImplementedError

    def outgoing_neighbors(self, node_id: Hashable) -> list[Node]:
        raise NotImplementedError

    def subgraph(self, node_ids: Iterable[Hashable]) -> Graph:
        raise NotImplementedError

    def connected_components(self) -> list[set[Hashable]]:
        raise NotImplementedError

    def is_connected(self) -> bool:
        raise NotImplementedError

    def has_cycle(self) -> bool:
        raise NotImplementedError