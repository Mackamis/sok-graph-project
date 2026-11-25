import pytest

from api.exceptions import (
    DuplicateIdError,
    GraphConstraintError,
    NodeHasEdgesError,
    NotFoundError,
)
from api.model import Edge, Graph, Node


def _graph_with_nodes(*node_ids, directed=True):
    graph = Graph(directed=directed)
    for node_id in node_ids:
        graph.add_node(Node(node_id))
    return graph


def test_graph_properties_are_read_only_live_views():
    graph = Graph()
    nodes = graph.nodes
    edges = graph.edges
    node = Node("a")
    graph.add_node(node)

    assert nodes["a"] is node
    # These invalid writes verify that read-only views reject mutation at runtime.
    with pytest.raises(TypeError):
        nodes["b"] = Node("b")  # type: ignore[reportIndexIssue]
    with pytest.raises(TypeError):
        edges["edge"] = Edge("edge", "a", "a")  # type: ignore[reportIndexIssue]
    with pytest.raises(AttributeError):
        setattr(graph, "directed", False)


def test_add_node_creates_empty_adjacency_and_rejects_duplicate_ids():
    graph = _graph_with_nodes("a")

    assert graph.edges_for("a") == []
    with pytest.raises(DuplicateIdError):
        graph.add_node(Node("a"))
    assert list(graph.nodes) == ["a"]


def test_add_edge_checks_before_mutating_and_keeps_edge_in_adjacency():
    graph = _graph_with_nodes("a", "b")
    edge = Edge("ab", "a", "b")

    with pytest.raises(NotFoundError):
        graph.add_edge(Edge("missing", "a", "missing"))
    assert graph.edges == {}
    assert graph.edges_for("a") == []

    graph.add_edge(edge)
    assert graph.get_edge("ab") is edge
    assert graph.edges_for("a") == [edge]
    assert graph.edges_for("b") == [edge]


def test_duplicate_edge_id_is_checked_before_missing_endpoints():
    graph = _graph_with_nodes("a", "b")
    graph.add_edge(Edge("edge", "a", "b"))

    with pytest.raises(DuplicateIdError):
        graph.add_edge(Edge("edge", "missing", "also-missing"))
    assert list(graph.edges) == ["edge"]


def test_directed_graph_allows_reverse_pair_but_rejects_same_pair():
    graph = _graph_with_nodes("a", "b")
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("ba", "b", "a"))

    with pytest.raises(GraphConstraintError):
        graph.add_edge(Edge("another-ab", "a", "b"))
    assert [edge.id for edge in graph.edges_for("a")] == ["ab", "ba"]


def test_undirected_graph_rejects_reverse_pair_and_duplicate_self_loop():
    graph = _graph_with_nodes("a", "b", directed=False)
    edge = Edge("ab", "a", "b")
    graph.add_edge(edge)

    with pytest.raises(GraphConstraintError):
        graph.add_edge(Edge("ba", "b", "a"))
    assert list(graph.edges.values()) == [edge]
    assert graph.edges_for("a") == [edge]
    assert graph.edges_for("b") == [edge]

    graph.add_edge(Edge("loop", "a", "a"))
    assert [edge.id for edge in graph.edges_for("a")] == ["ab", "loop"]
    with pytest.raises(GraphConstraintError):
        graph.add_edge(Edge("another-loop", "a", "a"))


def test_remove_edge_removes_both_registrations_and_self_loop_once():
    graph = _graph_with_nodes("a", "b")
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("loop", "a", "a"))

    graph.remove_edge("ab")
    graph.remove_edge("loop")

    assert graph.edges == {}
    assert graph.edges_for("a") == []
    assert graph.edges_for("b") == []
    graph.remove_node("a")
    graph.remove_node("b")
    assert graph.nodes == {}


def test_remove_edge_and_node_raise_for_missing_ids_or_incident_edges():
    graph = _graph_with_nodes("a", "b")
    graph.add_edge(Edge("ab", "a", "b"))

    with pytest.raises(NotFoundError):
        graph.remove_edge("missing")
    with pytest.raises(NotFoundError):
        graph.remove_node("missing")
    with pytest.raises(NodeHasEdgesError):
        graph.remove_node("a")
    assert "a" in graph.nodes
    assert graph.edges_for("a") == [graph.get_edge("ab")]


def test_getters_and_edges_for_raise_for_missing_ids():
    graph = Graph()

    with pytest.raises(NotFoundError):
        graph.get_node("missing")
    with pytest.raises(NotFoundError):
        graph.get_edge("missing")
    with pytest.raises(NotFoundError):
        graph.edges_for("missing")


def test_clear_empties_nodes_edges_and_adjacency():
    graph = _graph_with_nodes("a", "b")
    graph.add_edge(Edge("ab", "a", "b"))

    graph.clear()
    graph.add_node(Node("a"))

    assert graph.nodes == {"a": graph.get_node("a")}
    assert graph.edges == {}
    assert graph.edges_for("a") == []


def test_neighbors_include_incoming_and_outgoing_but_skip_self_loops():
    graph = _graph_with_nodes("a", "b", "c")
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("ca", "c", "a"))
    graph.add_edge(Edge("aa", "a", "a"))

    assert graph.neighbors("a") == [graph.get_node("b"), graph.get_node("c")]
    assert graph.outgoing_neighbors("a") == [graph.get_node("b")]


def test_neighbors_include_reciprocal_directed_pair_once():
    graph = _graph_with_nodes("a", "b")
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("ba", "b", "a"))

    assert graph.neighbors("a") == [graph.get_node("b")]
    assert graph.neighbors("b") == [graph.get_node("a")]


@pytest.mark.parametrize("method_name", ["neighbors", "outgoing_neighbors"])
def test_neighbor_methods_raise_for_missing_node(method_name):
    graph = Graph()

    with pytest.raises(NotFoundError):
        getattr(graph, method_name)("missing")


def test_undirected_outgoing_neighbors_match_neighbors():
    graph = _graph_with_nodes("a", "b", directed=False)
    graph.add_edge(Edge("ba", "b", "a"))

    assert graph.outgoing_neighbors("a") == graph.neighbors("a")
    assert graph.outgoing_neighbors("a") == [graph.get_node("b")]


def test_components_and_connectivity_handle_empty_and_isolated_nodes():
    empty = Graph()
    assert empty.connected_components() == []
    assert not empty.is_connected()

    graph = _graph_with_nodes("a", "b", "c")
    graph.add_edge(Edge("ab", "a", "b"))
    assert graph.connected_components() == [{"a", "b"}, {"c"}]
    assert not graph.is_connected()

    graph.add_edge(Edge("bc", "b", "c"))
    assert graph.connected_components() == [{"a", "b", "c"}]
    assert graph.is_connected()


def test_connected_components_use_weak_connectivity():
    graph = _graph_with_nodes("a", "b", "c")
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("cb", "c", "b"))

    assert graph.connected_components() == [{"a", "b", "c"}]
    assert graph.is_connected()


def test_subgraph_copies_selected_nodes_and_edges():
    graph = _graph_with_nodes("a", "b", "c")
    graph.get_node("a").set_attribute("color", "blue")
    graph.add_edge(Edge("ab", "a", "b", {"weight": 2}))

    subgraph = graph.subgraph(["b", "a"])

    assert subgraph.directed
    assert set(subgraph.nodes) == {"a", "b"}
    assert subgraph.get_node("a") == graph.get_node("a")
    assert subgraph.get_node("a") is not graph.get_node("a")
    assert subgraph.get_edge("ab") == graph.get_edge("ab")
    assert subgraph.get_edge("ab") is not graph.get_edge("ab")
    subgraph.get_node("a").set_attribute("color", "red")
    assert graph.get_node("a").attributes["color"] == "blue"

    with pytest.raises(NotFoundError):
        graph.subgraph(["missing"])


def test_undirected_subgraph_preserves_flag_and_filters_edges():
    graph = _graph_with_nodes("a", "b", "c", directed=False)
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("bc", "b", "c"))

    subgraph = graph.subgraph(["a", "a", "b"])
    empty_subgraph = graph.subgraph([])

    assert not subgraph.directed
    assert set(subgraph.nodes) == {"a", "b"}
    assert list(subgraph.edges) == ["ab"]
    assert not empty_subgraph.directed
    assert empty_subgraph.nodes == {}
    assert empty_subgraph.edges == {}


@pytest.mark.parametrize(
    ("directed", "edges", "expected"),
    [
        (True, [("ab", "a", "b"), ("bc", "b", "c")], False),
        (True, [("ab", "a", "b"), ("ba", "b", "a")], True),
        (True, [("loop", "a", "a")], True),
        (False, [("ab", "a", "b"), ("bc", "b", "c")], False),
        (False, [("ab", "a", "b"), ("bc", "b", "c"), ("ca", "c", "a")], True),
        (False, [("loop", "a", "a")], True),
    ],
)
def test_has_cycle(directed, edges, expected):
    node_ids = {endpoint for _, source, target in edges for endpoint in (source, target)}
    graph = _graph_with_nodes(*sorted(node_ids), directed=directed)
    for edge_id, source, target in edges:
        graph.add_edge(Edge(edge_id, source, target))

    assert graph.has_cycle() is expected


@pytest.mark.parametrize(
    ("directed", "edges"),
    [
        (True, [("ab", "a", "b"), ("ac", "a", "c"), ("bd", "b", "d")]),
        (False, [("ha", "h", "a"), ("hb", "h", "b"), ("hc", "h", "c")]),
    ],
)
def test_has_cycle_is_false_for_trees_and_stars(directed, edges):
    node_ids = {endpoint for _, source, target in edges for endpoint in (source, target)}
    graph = _graph_with_nodes(*sorted(node_ids), directed=directed)
    for edge_id, source, target in edges:
        graph.add_edge(Edge(edge_id, source, target))

    assert not graph.has_cycle()


@pytest.mark.parametrize(("directed", "expected"), [(True, False), (False, True)])
def test_diamond_cycle_depends_on_direction(directed, expected):
    graph = _graph_with_nodes("a", "b", "c", "d", directed=directed)
    for edge_id, source, target in (
        ("ab", "a", "b"),
        ("ac", "a", "c"),
        ("bd", "b", "d"),
        ("cd", "c", "d"),
    ):
        graph.add_edge(Edge(edge_id, source, target))

    assert graph.has_cycle() is expected


def test_has_cycle_detects_a_cycle_in_a_later_component_and_empty_graph():
    graph = _graph_with_nodes("a", "b", "c", "d")
    graph.add_edge(Edge("ab", "a", "b"))
    graph.add_edge(Edge("cd", "c", "d"))
    graph.add_edge(Edge("dc", "d", "c"))

    assert graph.has_cycle()
    assert not Graph().has_cycle()