from typing import Protocol, runtime_checkable
from fluss.engine.rpc_contract import DirectContract, RPCContract
from fluss.api.schema import (
    RekuestActionNodeBase,
)
from rekuest.client.client import Rekuest
from fluss.engine.errors import FlowLogicError
from arkitekt_runtime.task import Task


@runtime_checkable
class NodeContractor(Protocol):
    async def __call__(
        self,
        node: RekuestActionNodeBase,
        rekuest: Rekuest,
        task: "Task | None" = None,
    ) -> RPCContract: ...


async def arkicontractor(
    node: RekuestActionNodeBase, rekuest: Rekuest, task: "Task | None" = None
) -> RPCContract:
    """A contractor that can either spawn local, actors
    of use remote actors to perform the task

    The client looks the action up; the task, when there is one, is what the calls then go
    out through -- a call made while a task runs is that task's child, and only the task
    knows the socket and the assignment to make it one.
    """

    action = await rekuest.afind(hash=node.hash)
    if action.stateful:
        # A stateful action reads or changes the state of the agent that runs it, so rekuest
        # runs it only on a named agent. A graph flow has nowhere to name one yet (a Python
        # flow declares such steps as dependencies when it is deployed), so the run is
        # stopped here, before any step ran, and not at this step in its middle.
        raise FlowLogicError(
            f"{action.name} is stateful: it runs on an agent the run names, and a graph flow cannot name one yet. "
            "Call it from a Python flow, which binds the step to an agent when it is started."
        )

    return DirectContract(
        action=action, reference=node.id, rekuest=rekuest, task=task
    )
