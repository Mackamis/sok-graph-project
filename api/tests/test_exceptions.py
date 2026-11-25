import pytest

from api.exceptions import (
    DuplicateIdError,
    GraphConstraintError,
    GraphError,
    InvalidAttributeTypeError,
    InvalidIdError,
    NodeHasEdgesError,
    NotFoundError,
)


@pytest.mark.parametrize(
    ("error_type", "built_in_type"),
    [
        (DuplicateIdError, ValueError),
        (NotFoundError, KeyError),
        (InvalidAttributeTypeError, TypeError),
        (InvalidIdError, TypeError),
        (NodeHasEdgesError, ValueError),
        (GraphConstraintError, ValueError),
    ],
)
def test_graph_errors_have_expected_types_and_clean_messages(error_type, built_in_type):
    message = "example error message"
    error = error_type(message)

    assert isinstance(error, GraphError)
    assert isinstance(error, built_in_type)
    assert str(error) == message

    with pytest.raises(GraphError):
        raise error_type(message)

    with pytest.raises(built_in_type):
        raise error_type(message)
