from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from datetime import date
from types import MappingProxyType

from .exceptions import (
    DuplicateIdError,
    GraphConstraintError,
    InvalidAttributeTypeError,
    InvalidIdError,
    NodeHasEdgesError,
    NotFoundError,
)

AttrValue = int | str | float | date


def _validate_id(value: object, name: str) -> None:
    """Raise InvalidIdError unless value is non-None and actually hashable."""
    if value is None:
        raise InvalidIdError(f"{name} cannot be None")
    try:
        hash(value)
    except TypeError as error:
        raise InvalidIdError(
            f"{name} must be hashable, not {type(value).__name__}"
        ) from error


def _validate_attribute_key(key: object) -> None:
    """Raise InvalidAttributeTypeError unless key is a string."""
    if not isinstance(key, str):
        raise InvalidAttributeTypeError(
            f"Attribute key {key!r} must be str, not {type(key).__name__}"
        )


def _validate_attribute(key: object, value: object) -> None:
    """Validate a key and require an exact int, str, float, or date value."""
    _validate_attribute_key(key)
    if type(value) not in (int, str, float, date):
        raise InvalidAttributeTypeError(
            f"Attribute {key!r} must be int, str, float, or date, "
            f"not {type(value).__name__}"
        )


class _AttributeOwner:
    """Provide shared attribute storage and identity behavior for graph items."""

    _id: Hashable

    def __init__(self, attributes: Mapping[str, AttrValue] | None = None) -> None:
        """Copy and validate the optional initial attribute mapping."""
        self._attributes: dict[str, AttrValue] = {}
        if attributes is not None:
            for key, value in attributes.items():
                self.set_attribute(key, value)

    def __eq__(self, other: object) -> bool:
        """Compare graph items by concrete class and ID, ignoring attributes."""
        if not isinstance(other, _AttributeOwner) or type(self) is not type(other):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Return a hash based on concrete class and ID."""
        return hash((type(self), self._id))

    @property
    def attributes(self) -> Mapping[str, AttrValue]:
        """Return a live, read-only view of the item's attributes."""
        return MappingProxyType(self._attributes)

    def set_attribute(self, key: str, value: AttrValue) -> None:
        """Add or replace an attribute after validating its key and value."""
        _validate_attribute(key, value)
        self._attributes[key] = value

    def remove_attribute(self, key: str) -> None:
        """Remove an attribute by key.

        Raises:
            InvalidAttributeTypeError: If key is not a string.
            NotFoundError: If key is not present.
        """
        _validate_attribute_key(key)
        try:
            del self._attributes[key]
        except KeyError:
            raise NotFoundError(f"Attribute {key!r} not found") from None


class Node(_AttributeOwner):
    """A graph node with a hashable ID and validated attributes."""

    def __init__(
        self,
        node_id: Hashable,
        attributes: Mapping[str, AttrValue] | None = None,
    ) -> None:
        """Create a node, copying and validating its optional attributes.

        Raises:
            InvalidIdError: If node_id is None or unhashable.
            InvalidAttributeTypeError: If an attribute key or value is invalid.
        """
        _validate_id(node_id, "Node ID")
        self._id = node_id
        super().__init__(attributes)

    @property
    def id(self) -> Hashable:
        """Return this node's immutable ID."""
        return self._id

    def __repr__(self) -> str:
        """Return a representation containing the node ID and attributes."""
        return f"Node(id={self.id!r}, attributes={dict(self.attributes)!r})"

    def copy(self) -> Node:
        """Return a new node with the same ID and an independent attribute map."""
        return Node(self.id, self.attributes)


class Edge(_AttributeOwner):
    """A graph edge with an ID, source and target node IDs, and attributes."""

    def __init__(
        self,
        edge_id: Hashable,
        source: Hashable,
        target: Hashable,
        attributes: Mapping[str, AttrValue] | None = None,
    ) -> None:
        """Create an edge, validating its IDs and copying its optional attributes.

        Raises:
            InvalidIdError: If an ID is None or unhashable.
            InvalidAttributeTypeError: If an attribute key or value is invalid.
        """
        _validate_id(edge_id, "Edge ID")
        _validate_id(source, "Edge source ID")
        _validate_id(target, "Edge target ID")
        self._id = edge_id
        self._source = source
        self._target = target
        super().__init__(attributes)

    @property
    def id(self) -> Hashable:
        """Return this edge's immutable ID."""
        return self._id

    @property
    def source(self) -> Hashable:
        """Return the immutable ID of this edge's source node."""
        return self._source

    @property
    def target(self) -> Hashable:
        """Return the immutable ID of this edge's target node."""
        return self._target

    def __repr__(self) -> str:
        """Return a representation containing the edge IDs and attributes."""
        return (
            f"Edge(id={self.id!r}, source={self.source!r}, "
            f"target={self.target!r}, attributes={dict(self.attributes)!r})"
        )

    def copy(self) -> Edge:
        """Return a new edge with the same IDs and an independent attribute map."""
        return Edge(self.id, self.source, self.target, self.attributes)


class Graph:
    """A collection of nodes and edges, optionally treating edges as directed."""

    def __init__(self, directed: bool = True) -> None:
        """Create an empty graph, directed by default."""
        self._directed = directed
        self._nodes: dict[Hashable, Node] = {}
        self._edges: dict[Hashable, Edge] = {}
        self._adjacency: dict[Hashable, dict[Hashable, None]] = {}

    @property
    def directed(self) -> bool:
        """Return whether edges are directed; this property is read-only."""
        return self._directed

    @property
    def nodes(self) -> Mapping[Hashable, Node]:
        """Return a read-only mapping of nodes keyed by node ID."""
        return MappingProxyType(self._nodes)

    @property
    def edges(self) -> Mapping[Hashable, Edge]:
        """Return a read-only mapping of edges keyed by edge ID."""
        return MappingProxyType(self._edges)

    def add_node(self, node: Node) -> None:
        """Store a node, raising DuplicateIdError if its ID is already present.

        The graph stores the supplied object without copying it. If another
        graph stores the same node, both graphs see its attribute changes.
        """
        if node.id in self._nodes:
            raise DuplicateIdError(f"Node ID {node.id!r} already exists")
        self._nodes[node.id] = node
        self._adjacency[node.id] = {}

    def add_edge(self, edge: Edge) -> None:
        """Store an edge in the graph without making a copy.

        If another graph stores the same edge, both graphs see its attribute
        changes.

        Raises:
            DuplicateIdError: If an edge with this ID already exists.
            NotFoundError: If either endpoint is not in the graph.
            GraphConstraintError: If an edge already connects this pair.
        """
        if edge.id in self._edges:
            raise DuplicateIdError(f"Edge ID {edge.id!r} already exists")
        if edge.source not in self._nodes:
            raise NotFoundError(f"Node {edge.source!r} not found")
        if edge.target not in self._nodes:
            raise NotFoundError(f"Node {edge.target!r} not found")

        source_edges = self._adjacency[edge.source]
        target_edges = self._adjacency[edge.target]
        incident_edge_ids = (
            source_edges if len(source_edges) <= len(target_edges) else target_edges
        )
        for existing_id in incident_edge_ids:
            existing = self._edges[existing_id]
            if self._same_edge_pair(existing, edge):
                raise GraphConstraintError(
                    f"An edge already connects {edge.source!r} and {edge.target!r}"
                )

        self._edges[edge.id] = edge
        source_edges[edge.id] = None
        if edge.target != edge.source:
            target_edges[edge.id] = None

    def _same_edge_pair(self, existing: Edge, candidate: Edge) -> bool:
        same_direction = (
            existing.source == candidate.source
            and existing.target == candidate.target
        )
        if self._directed or same_direction:
            return same_direction
        return (
            existing.source == candidate.target
            and existing.target == candidate.source
        )

    def remove_node(self, node_id: Hashable) -> None:
        """Remove a node by ID.

        Raises:
            NotFoundError: If node_id is not in the graph.
            NodeHasEdgesError: If the node still has incident edges.
        """
        if node_id not in self._nodes:
            raise NotFoundError(f"Node {node_id!r} not found")
        if self._adjacency[node_id]:
            raise NodeHasEdgesError(f"Node {node_id!r} still has edges")
        del self._nodes[node_id]
        del self._adjacency[node_id]

    def remove_edge(self, edge_id: Hashable) -> None:
        """Remove an edge by ID, raising NotFoundError if it is absent."""
        try:
            edge = self._edges[edge_id]
        except KeyError:
            raise NotFoundError(f"Edge {edge_id!r} not found") from None

        del self._adjacency[edge.source][edge_id]
        if edge.target != edge.source:
            del self._adjacency[edge.target][edge_id]
        del self._edges[edge_id]

    def get_node(self, node_id: Hashable) -> Node:
        """Return the node with this ID, raising NotFoundError if absent."""
        try:
            return self._nodes[node_id]
        except KeyError:
            raise NotFoundError(f"Node {node_id!r} not found") from None

    def get_edge(self, edge_id: Hashable) -> Edge:
        """Return the edge with this ID, raising NotFoundError if absent."""
        try:
            return self._edges[edge_id]
        except KeyError:
            raise NotFoundError(f"Edge {edge_id!r} not found") from None

    def edges_for(self, node_id: Hashable) -> list[Edge]:
        """Return incident edges in insertion order, including a self-loop once.

        Raises NotFoundError if node_id is not in the graph.
        """
        if node_id not in self._nodes:
            raise NotFoundError(f"Node {node_id!r} not found")
        return [self._edges[edge_id] for edge_id in self._adjacency[node_id]]

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()

    def neighbors(self, node_id: Hashable) -> list[Node]:
        """Return adjacent nodes in edge insertion order, each exactly once.

        Incoming and outgoing edges both count. A node is never its own
        neighbor, so self-loops are ignored. Raises NotFoundError if node_id
        does not exist.
        """
        if node_id not in self._nodes:
            raise NotFoundError(f"Node {node_id!r} not found")

        result: list[Node] = []
        seen: set[Hashable] = set()
        for edge_id in self._adjacency[node_id]:
            edge = self._edges[edge_id]
            neighbor_id = edge.target if edge.source == node_id else edge.source
            if neighbor_id != node_id and neighbor_id not in seen:
                seen.add(neighbor_id)
                result.append(self._nodes[neighbor_id])
        return result

    def outgoing_neighbors(self, node_id: Hashable) -> list[Node]:
        """Return every node reachable from node_id over one outgoing edge, each once.

        In an undirected graph every edge can be followed in both directions,
        so this equals neighbors(). Self-loops are ignored. Raises
        NotFoundError if node_id does not exist.
        """
        if node_id not in self._nodes:
            raise NotFoundError(f"Node {node_id!r} not found")

        result: list[Node] = []
        seen: set[Hashable] = set()
        for edge_id in self._adjacency[node_id]:
            edge = self._edges[edge_id]
            if self._directed and edge.source != node_id:
                continue
            neighbor_id = edge.target if edge.source == node_id else edge.source
            if neighbor_id != node_id and neighbor_id not in seen:
                seen.add(neighbor_id)
                result.append(self._nodes[neighbor_id])
        return result

    def connected_components(self) -> list[set[Hashable]]:
        """Return the weakly connected components as sets of node ids.

        Edge direction is ignored: two nodes share a component if a path
        joins them when every edge is treated as undirected. Isolated nodes
        form singleton components. An empty graph has no components.
        """
        unseen = set(self._nodes)
        components: list[set[Hashable]] = []
        for start in self._nodes:
            if start not in unseen:
                continue
            component = {start}
            unseen.remove(start)
            pending = [start]
            while pending:
                current = pending.pop()
                for neighbor in self.neighbors(current):
                    if neighbor.id in unseen:
                        unseen.remove(neighbor.id)
                        component.add(neighbor.id)
                        pending.append(neighbor.id)
            components.append(component)
        return components

    def subgraph(self, node_ids: Iterable[Hashable]) -> Graph:
        """Return a graph containing copies of the selected nodes and their edges.

        The returned graph preserves this graph's directedness and includes edges
        whose endpoints are both selected. Its nodes and edges are copies, so
        changes to the subgraph do not affect the original graph.

        Raises NotFoundError if any ID in node_ids is not in the graph.
        """
        selected: dict[Hashable, None] = {}
        for node_id in node_ids:
            if node_id not in self._nodes:
                raise NotFoundError(f"Node {node_id!r} not found")
            selected[node_id] = None

        result = Graph(self._directed)
        for node_id in selected:
            result.add_node(self._nodes[node_id].copy())
        for edge in self._edges.values():
            if edge.source in selected and edge.target in selected:
                result.add_edge(edge.copy())
        return result

    def is_connected(self) -> bool:
        """Return True if the graph has exactly one weakly connected component.

        Edge direction is ignored (see connected_components). An empty graph
        is not connected.
        """
        return bool(self._nodes) and len(self.connected_components()) == 1

    def has_cycle(self) -> bool:
        """Return True if the graph contains at least one cycle.

        Directed graph: a cycle that follows edge direction, such as
        A->B->A or a self-loop. Undirected graph: a closed path that never
        reuses an edge; a self-loop counts. Directed and undirected graphs
        need different detection algorithms.
        """
        if self._directed:
            return self._has_directed_cycle()
        return self._has_undirected_cycle()

    def _has_directed_cycle(self) -> bool:
        indegree = {node_id: 0 for node_id in self._nodes}
        outgoing: dict[Hashable, list[Hashable]] = {
            node_id: [] for node_id in self._nodes
        }
        for edge in self._edges.values():
            outgoing[edge.source].append(edge.target)
            indegree[edge.target] += 1

        ready_nodes: list[Hashable] = [
            node_id for node_id, degree in indegree.items() if degree == 0
        ]
        removed = 0
        while ready_nodes:
            node_id = ready_nodes.pop()
            removed += 1
            for target in outgoing[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready_nodes.append(target)
        return removed != len(self._nodes)

    def _has_undirected_cycle(self) -> bool:
        visited: set[Hashable] = set()
        for start in self._nodes:
            if start in visited:
                continue
            visited.add(start)
            pending: list[tuple[Hashable, Hashable | None]] = [(start, None)]
            while pending:
                node_id, parent_edge_id = pending.pop()
                for edge_id in self._adjacency[node_id]:
                    if edge_id == parent_edge_id:
                        continue
                    edge = self._edges[edge_id]
                    neighbor_id = edge.target if edge.source == node_id else edge.source
                    if neighbor_id in visited:
                        return True
                    visited.add(neighbor_id)
                    pending.append((neighbor_id, edge_id))
        return False