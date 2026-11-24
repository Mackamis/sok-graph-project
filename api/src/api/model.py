from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from datetime import date
from types import MappingProxyType

from .exceptions import InvalidAttributeTypeError, InvalidIdError, NotFoundError

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
        raise NotImplementedError

    @property
    def directed(self) -> bool:
        """Return whether edges are directed; this property is read-only."""
        raise NotImplementedError

    @property
    def nodes(self) -> Mapping[Hashable, Node]:
        """Return a read-only mapping of nodes keyed by node ID."""
        raise NotImplementedError

    @property
    def edges(self) -> Mapping[Hashable, Edge]:
        """Return a read-only mapping of edges keyed by edge ID."""
        raise NotImplementedError

    def add_node(self, node: Node) -> None:
        """Add a node, raising DuplicateIdError if its ID is already present."""
        raise NotImplementedError

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph.

        Raises:
            DuplicateIdError: If an edge with this ID already exists.
            NotFoundError: If either endpoint is not in the graph.
            GraphConstraintError: If an edge already connects this pair.
        """
        raise NotImplementedError

    def remove_node(self, node_id: Hashable) -> None:
        """Remove a node by ID.

        Raises:
            NotFoundError: If node_id is not in the graph.
            NodeHasEdgesError: If the node still has incident edges.
        """
        raise NotImplementedError

    def remove_edge(self, edge_id: Hashable) -> None:
        """Remove an edge by ID, raising NotFoundError if it is absent."""
        raise NotImplementedError

    def get_node(self, node_id: Hashable) -> Node:
        """Return the node with this ID, raising NotFoundError if absent."""
        raise NotImplementedError

    def get_edge(self, edge_id: Hashable) -> Edge:
        """Return the edge with this ID, raising NotFoundError if absent."""
        raise NotImplementedError

    def edges_for(self, node_id: Hashable) -> list[Edge]:
        """Return edges incident to node_id, including a self-loop only once.

        Raises NotFoundError if node_id is not in the graph.
        """
        raise NotImplementedError

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        raise NotImplementedError

    def neighbors(self, node_id: Hashable) -> list[Node]:
        """Return every node adjacent to node_id, each exactly once.

        Incoming and outgoing edges both count. A node is never its own
        neighbor, so self-loops are ignored. Raises NotFoundError if node_id
        does not exist.
        """
        raise NotImplementedError

    def outgoing_neighbors(self, node_id: Hashable) -> list[Node]:
        """Return every node reachable from node_id over one outgoing edge, each once.

        In an undirected graph every edge can be followed in both directions,
        so this equals neighbors(). Self-loops are ignored. Raises
        NotFoundError if node_id does not exist.
        """
        raise NotImplementedError

    def connected_components(self) -> list[set[Hashable]]:
        """Return the weakly connected components as sets of node ids.

        Edge direction is ignored: two nodes share a component if a path
        joins them when every edge is treated as undirected. Isolated nodes
        form singleton components. An empty graph has no components.
        """
        raise NotImplementedError
    
    def subgraph(self, node_ids: Iterable[Hashable]) -> Graph:
        """Return a graph containing copies of the selected nodes and their edges.

        The returned graph preserves this graph's directedness and includes edges
        whose endpoints are both selected. Its nodes and edges are copies, so
        changes to the subgraph do not affect the original graph.

        Raises NotFoundError if any ID in node_ids is not in the graph.
        """
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Return True if the graph has exactly one weakly connected component.

        Edge direction is ignored (see connected_components). An empty graph
        is not connected.
        """
        raise NotImplementedError

    def has_cycle(self) -> bool:
        """Return True if the graph contains at least one cycle.

        Directed graph: a cycle that follows edge direction, such as
        A->B->A or a self-loop. Undirected graph: a closed path that never
        reuses an edge; a self-loop counts. Directed and undirected graphs
        need different detection algorithms.
        """
        raise NotImplementedError