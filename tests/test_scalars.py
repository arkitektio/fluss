"""Tests for the scalars module."""

from fluss_next.scalars import NodeException
import pytest
from pydantic import BaseModel


class NodeWithError(BaseModel):
    """Test model to validate the NodeException scalar."""

    error: NodeException


def test_node_exception() -> None:
    """Test the NodeException scalar."""
    # Test valid input
    valid_input = "This is a test exception"
    exception = NodeWithError(error=valid_input).error  # type: ignore[arg-type]
    assert exception == valid_input

    # Test invalid input
    invalid_input = 12345
    with pytest.raises(ValueError):
        NodeWithError(error=invalid_input)  # type: ignore[arg-type]
