from typing import Protocol, runtime_checkable
from fluss.engine.rpc_contract import DirectContract, RPCContract
from fluss.api.schema import (
    RekuestActionNodeBase,
)
from rekuest.api.schema import afind
from rekuest.actors.base import Actor


@runtime_checkable
class NodeContractor(Protocol):
    async def __call__(
        self, node: RekuestActionNodeBase, actor: Actor
    ) -> RPCContract: ...


async def arkicontractor(node: RekuestActionNodeBase, actor: Actor) -> RPCContract:
    """A contractor that can either spawn local, actors
    of use remote actors to perform the task


    """

    action = await afind(hash=node.hash)

    return DirectContract(action=action, reference=node.id)
