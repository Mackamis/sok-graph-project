from datetime import date, datetime

import pytest

from api.exceptions import InvalidAttributeTypeError, NotFoundError
from api.model import Edge, Node


def _new_entity(entity_type, attributes=None):
    if entity_type is Node:
        return Node("node", attributes)
    return Edge("edge", "source", "target", attributes)


def _apply_attribute(entity_type, operation, key, value):
    if operation == "constructor":
        return _new_entity(entity_type, {key: value})

    entity = _new_entity(entity_type)
    entity.set_attribute(key, value)
    return entity


@pytest.mark.parametrize("entity_type", [Node, Edge])
@pytest.mark.parametrize("operation", ["constructor", "setter"])
@pytest.mark.parametrize(
    "value",
    [42, "text", 3.14, date(2026, 1, 2)],
    ids=["int", "str", "float", "date"],
)
def test_attributes_accept_supported_exact_types(entity_type, operation, value):
    entity = _apply_attribute(entity_type, operation, "field", value)

    assert entity.attributes["field"] == value


@pytest.mark.parametrize("entity_type", [Node, Edge])
@pytest.mark.parametrize("operation", ["constructor", "setter"])
@pytest.mark.parametrize(
    "value",
    [True, False, datetime(2026, 1, 2), [], None, {}],
    ids=["true", "false", "datetime", "list", "none", "dict"],
)
def test_attributes_reject_unsupported_types(entity_type, operation, value):
    with pytest.raises(InvalidAttributeTypeError) as error:
        _apply_attribute(entity_type, operation, "field", value)

    assert str(error.value) == (
        f"Attribute 'field' must be int, str, float, or date, "
        f"not {type(value).__name__}"
    )


@pytest.mark.parametrize("entity_type", [Node, Edge])
@pytest.mark.parametrize("operation", ["constructor", "setter"])
def test_attributes_reject_non_string_keys(entity_type, operation):
    with pytest.raises(InvalidAttributeTypeError) as error:
        _apply_attribute(entity_type, operation, 42, 1)

    assert str(error.value) == "Attribute key 42 must be str, not int"


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_constructor_rejects_multiple_attributes_if_one_is_invalid(entity_type):
    attributes = {"valid": 1, "invalid": [], "also_valid": "text"}

    with pytest.raises(InvalidAttributeTypeError, match="Attribute 'invalid'.*list"):
        _new_entity(entity_type, attributes)


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_failed_set_attribute_preserves_existing_value(entity_type):
    entity = _new_entity(entity_type, {"field": "old"})

    with pytest.raises(InvalidAttributeTypeError):
        entity.set_attribute("field", [])

    assert entity.attributes["field"] == "old"


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_remove_attribute_succeeds(entity_type):
    entity = _new_entity(entity_type, {"field": "value"})

    entity.remove_attribute("field")

    assert "field" not in entity.attributes


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_remove_attribute_raises_for_missing_key(entity_type):
    entity = _new_entity(entity_type)

    with pytest.raises(NotFoundError, match="Attribute 'missing' not found"):
        entity.remove_attribute("missing")


@pytest.mark.parametrize("entity_type", [Node, Edge])
def test_remove_attribute_rejects_non_string_key(entity_type):
    entity = _new_entity(entity_type, {"field": "value"})

    with pytest.raises(InvalidAttributeTypeError, match="Attribute key 42 must be str"):
        entity.remove_attribute(42)

    assert entity.attributes["field"] == "value"
