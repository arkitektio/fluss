"""Test the fake workspace creation"""

import pytest
from fluss.api.schema import FlussApi  # noqa: F401 (the client carries the operations)
from dokker import Deployment


@pytest.mark.integration
def test_creation(deployed_app) -> None:  # noqa: ANN001
    """Test the creation of a workspace"""
    deployed_app.fluss.create_workspace(True, title="Test", description="Test")
