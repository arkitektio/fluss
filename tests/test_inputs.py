"""Tests for the inputs module."""

from fluss_next.api.schema import ArgPortInput, PortKind


def test_int_port() -> None:
    """Test the Input Port."""
    ArgPortInput(key="1234", kind=PortKind.INT, nullable=False)


def test_float_port() -> None:
    """Test the Float Port."""
    ArgPortInput(key="1234", kind=PortKind.FLOAT, nullable=False)
