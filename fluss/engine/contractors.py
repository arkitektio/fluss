from typing import Protocol, runtime_checkable
from fluss.engine.rpc_contract import DirectContract, RPCContract
from fluss.api.schema import (
    RekuestActionNodeBase,
)
from rekuest.client.client import Rekuest
from rekuest.task import Task


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

    return DirectContract(
        action=action, reference=node.id, rekuest=rekuest, task=task
    )
