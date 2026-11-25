import pytest

from api.exceptions import InvalidIdError
from api.model import Edge, Node


@pytest.mark.parametrize(
    ("constructor", "name"),
    [
        pytest.param(lambda value: Node(value), "Node ID", id="node-id"),
        pytest.param(
            lambda value: Edge(value, "source", "target"),
            "Edge ID",
            id="edge-id",
        ),
        pytest.param(
            lambda value: Edge("edge", value, "target"),
            "Edge source ID",
            id="edge-source",
        ),
        pytest.param(
            lambda value: Edge("edge", "source", value),
            "Edge target ID",
            id="edge-target",
        ),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param([1, 2], id="list"),
        pytest.param(([1],), id="tuple-containing-list"),
        pytest.param(None, id="none"),
    ],
)
def test_ids_must_be_hashable_and_not_none(constructor, name, value):
    with pytest.raises(InvalidIdError) as error:
        constructor(value)

    assert isinstance(error.value, TypeError)
    expected_message = (
        f"{name} cannot be None"
        if value is None
        else f"{name} must be hashable, not {type(value).__name__}"
    )
    assert str(error.value) == expected_message
