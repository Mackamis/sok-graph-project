from operator import setitem

import pytest

from api.model import Edge, Node


def _new_entity(entity_type, attributes=None):
    if entity_type is Node:
        return Node("node", attributes)
    return Edge("edge", "source", "target", attributes)


def _entity_with_id(entity_type, identifier, attributes=None):
    if entity_type is Node:
        return Node(identifier, attributes)
    return Edge(identifier, "source", "target", attributes)


def test_node_and_edge_store_their_identifiers():
    node = Node("node-id")
    edge = Edge("edge-id", "source-id", "target-id")

    assert node.id == "node-id"
    assert edge.id == "edge-id"
    assert edge.source == "source-id"
    assert edge.target == "target-id"


def test_identifiers_are_read_only():
    node = Node("node-id")
    edge = Edge("edge-id", "source-id", "target-id")

    for entity, name, value in (
        (node, "id", "other-node"),
        (edge, "id", "other-edge"),
        (edge, "source", "other-source"),
        (edge, "target", "other-target"),
    ):
        with pytest.raises(AttributeError):
            setattr(entity, name, value)


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_attributes_view_is_read_only(entity_type):
    entity = _new_entity(entity_type)

    with pytest.raises(TypeError):
        setitem(entity.attributes, "field", "value")


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_mutating_constructor_mapping_does_not_change_attributes(entity_type):
    attributes = {"field": "before"}
    entity = _new_entity(entity_type, attributes)

    attributes["field"] = "after"
    attributes["added"] = "new"
    del attributes["field"]

    assert dict(entity.attributes) == {"field": "before"}


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_same_class_entities_with_same_id_are_equal(entity_type):
    first = _entity_with_id(entity_type, "same-id", {"field": "value"})
    second = _entity_with_id(entity_type, "same-id", {"field": "value"})

    assert first == second


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_attributes_do_not_affect_equality(entity_type):
    first = _entity_with_id(entity_type, "same-id", {"first": 1})
    second = _entity_with_id(entity_type, "same-id", {"second": 2})

    assert first == second


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_different_ids_are_not_equal(entity_type):
    first = _entity_with_id(entity_type, "first")
    second = _entity_with_id(entity_type, "second")

    assert first != second


def test_node_and_edge_with_same_id_are_not_equal():
    assert Node("same-id") != Edge("same-id", "source", "target")


@pytest.mark.parametrize("entity_type", [Node, Edge])
@pytest.mark.parametrize("other", [1, None, "node"])
def test_comparison_with_other_types_is_false(entity_type, other):
    assert _entity_with_id(entity_type, "node") != other


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_equal_entities_have_equal_hashes_and_work_as_keys(entity_type):
    first = _entity_with_id(entity_type, "same-id", {"field": "first"})
    second = _entity_with_id(entity_type, "same-id", {"field": "second"})

    assert hash(first) == hash(second)
    assert len({first, second}) == 1
    assert {first: "value"}[second] == "value"


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_hash_does_not_change_when_attributes_change(entity_type):
    entity = _new_entity(entity_type)
    original_hash = hash(entity)

    entity.set_attribute("field", "value")

    assert hash(entity) == original_hash


def test_repr_includes_node_identity_and_attributes():
    assert repr(Node("node", {"color": "blue"})) == (
        "Node(id='node', attributes={'color': 'blue'})"
    )


def test_repr_includes_edge_identity_endpoints_and_attributes():
    assert repr(Edge("edge", "source", "target", {"weight": 2})) == (
        "Edge(id='edge', source='source', target='target', "
        "attributes={'weight': 2})"
    )


def test_node_copy_is_equal_but_independent():
    node = Node("node", {"color": "blue"})

    copied = node.copy()

    assert copied == node
    assert copied is not node
    copied.set_attribute("color", "red")
    assert node.attributes == {"color": "blue"}
    assert copied.attributes == {"color": "red"}


def test_edge_copy_is_equal_but_independent_and_keeps_endpoints():
    edge = Edge("edge", "source", "target", {"weight": 2})

    copied = edge.copy()

    assert copied == edge
    assert copied is not edge
    assert (copied.source, copied.target) == ("source", "target")
    copied.set_attribute("weight", 3)
    assert edge.attributes == {"weight": 2}
    assert copied.attributes == {"weight": 3}