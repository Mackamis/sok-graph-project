class GraphError(Exception):
    """Base exception for all graph model domain errors."""


class DuplicateIdError(GraphError, ValueError):
    """Raised when adding a node or edge with an ID that already exists."""


class NotFoundError(GraphError, KeyError):
    """Raised when a referenced node, edge, or attribute key does not exist."""


class InvalidAttributeTypeError(GraphError, TypeError):
    """Raised when an attribute value is not an exact int, str, float, or date."""


class NodeHasEdgesError(GraphError, ValueError):
    """Raised when attempting to remove a node that still has connected edges."""


class GraphConstraintError(GraphError, ValueError):
    """Raised when an operation violates a graph structural constraint."""