"""A flow run is a workflow, and its nodes key their calls so a resumed run finds them again.

A flow's nodes call concurrently: the steps their calls take differ from one run to the
next, the node and how often it has called do not.
"""

from typing import Any

import pytest
from arkitekt_spec.actions import Execution

from fluss.engine.rpc_contract import DirectContract


class RecordingTask:
    def __init__(self) -> None:
        self.keys: list[str | None] = []

    async def acall_raw(self, **kwargs: Any) -> dict[str, Any]:
        self.keys.append(kwargs.get("call_key"))
        return {}


class RootClient:
    def __init__(self) -> None:
        self.kwargs: list[dict[str, Any]] = []

    async def acall_raw(self, **kwargs: Any) -> dict[str, Any]:
        self.kwargs.append(kwargs)
        return {}


def test_both_flow_runners_are_workflows() -> None:
    from arkitekt_spec.declare.assemble import assemble

    from fluss.engine import fluss_actions

    flow = assemble(fluss_actions).implementations["run_flow"]
    assert flow.execution == Execution.WORKFLOW

    pytest.importorskip("fluss_monty")
    from fluss.engine.python import fluss_python_actions

    python = assemble(fluss_python_actions).implementations["run_python_flow"]
    assert python.execution == Execution.WORKFLOW


@pytest.mark.asyncio
async def test_a_nodes_calls_are_keyed_by_node_and_occurrence() -> None:
    task = RecordingTask()
    first = DirectContract.model_construct(
        action=object(), reference="node-a", rekuest=None, task=task
    )
    other = DirectContract.model_construct(
        action=object(), reference="node-b", rekuest=None, task=task
    )

    await first.acall_raw(kwargs={})
    await other.acall_raw(kwargs={})
    await first.acall_raw(kwargs={})

    assert task.keys == ["node-a:1", "node-b:1", "node-a:2"]


@pytest.mark.asyncio
async def test_a_root_call_outside_any_task_has_no_key() -> None:
    client = RootClient()
    contract = DirectContract.model_construct(
        action=object(), reference="node-a", rekuest=client, task=None
    )

    await contract.acall_raw(kwargs={})

    assert "call_key" not in client.kwargs[0]
