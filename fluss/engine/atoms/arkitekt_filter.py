import logging

from fluss.api.schema import RekuestFilterActionNode
from fluss.engine.atoms.generic import (
    FilterAtom,
)
from fluss.engine.atoms.helpers import node_to_reference
from fluss.engine.events import InEvent
from fluss.engine.rpc_contract import RPCContract

logger = logging.getLogger(__name__)


class ArkitektFilterAtom(FilterAtom):
    node: RekuestFilterActionNode
    contract: RPCContract

    async def filter(self, event: InEvent) -> bool:
        kwargs = self.set_values

        stream_one = self.node.ins[0]
        for arg, item in zip(event.value, stream_one, strict=False):
            kwargs[item.key] = arg

        returns = await self.contract.acall_raw(
            kwargs=kwargs,
            reference=node_to_reference(self.node, event),
        )
        return all([r for r in returns.values()])
