from typing import Protocol, runtime_checkable
from fluss.engine.rpc_contract import DirectContract, RPCContract
from fluss.api.schema import (
    RekuestActionNodeBase,
)
from rekuest.rekuest import Rekuest


@runtime_checkable
class NodeContractor(Protocol):
    async def __call__(
        self, node: RekuestActionNodeBase, rekuest: Rekuest
    ) -> RPCContract: ...


async def arkicontractor(node: RekuestActionNodeBase, rekuest: Rekuest) -> RPCContract:
    """A contractor that can either spawn local, actors
    of use remote actors to perform the task


    """

    action = await rekuest.afind(hash=node.hash)

    return DirectContract(action=action, reference=node.id, rekuest=rekuest)
