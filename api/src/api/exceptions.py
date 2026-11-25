class GraphError(Exception):
    """Base exception for all graph model domain errors."""


class DuplicateIdError(GraphError, ValueError):
    """Raised when adding a node or edge with an ID that already exists."""


class NotFoundError(GraphError, KeyError):
    """Raised when a referenced node, edge, or attribute key does not exist."""

    def __str__(self) -> str:
        if len(self.args) == 1:
            return str(self.args[0])
        return super().__str__()


class InvalidAttributeTypeError(GraphError, TypeError):
    """Raised when an attribute key or value has an unsupported type."""


class InvalidIdError(GraphError, TypeError):
    """Raised when an ID is None or cannot be hashed."""


class NodeHasEdgesError(GraphError, ValueError):
    """Raised when attempting to remove a node that still has connected edges."""


class GraphConstraintError(GraphError, ValueError):
    """Raised when an operation violates a graph structural constraint."""