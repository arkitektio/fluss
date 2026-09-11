"""Test the fake workspace creation"""

import pytest
from fluss_next.api.schema import create_workspace
from dokker import Deployment


@pytest.mark.integration
def test_creation(deployed_app: Deployment) -> None:
    """Test the creation of a workspace"""
    create_workspace(True, title="Test", description="Test")
