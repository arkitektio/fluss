import json
import pytest
from fluss.api.schema import (
    FlowFragment,
)
from .utils import build_relative
from .flows import add_three_flow


@pytest.mark.serialize
def test_stream(add_three_flow: FlowFragment):

    for node in add_three_flow.graph.nodes:
        for stream in node.instream:
            for stream_item in stream:
                stream_item.mock()
