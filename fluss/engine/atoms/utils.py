from typing import Awaitable, Callable, Dict
from fluss.engine.atoms.transformation.buffer_count import BufferCountAtom
from rekuest.messages import Assign
from fluss.api.schema import (
    RekuestFilterActionNode,
    RekuestMapActionNode,
    ReactiveNode,
    BaseGraphNodeBase,
    MapStrategy,
    ReactiveImplementation,
    ActionKind,
)
import asyncio
from fluss.engine.atoms.arkitekt import (
    ArkitektMapAtom,
    ArkitektMergeMapAtom,
    ArkitektAsCompletedAtom,
    ArkitektOrderedAtom,
)
from fluss.engine.atoms.arkitekt_filter import ArkitektFilterAtom
from fluss.engine.atoms.transformation.chunk import ChunkAtom
from fluss.engine.atoms.transformation.buffer_complete import BufferCompleteAtom
from fluss.engine.atoms.transformation.split import SplitAtom
from fluss.engine.atoms.transformation.omit import OmitAtom
from fluss.engine.atoms.combination.zip import ZipAtom
from fluss.engine.atoms.transformation.filter import FilterAtom
from fluss.engine.atoms.combination.withlatest import WithLatestAtom
from fluss.engine.atoms.combination.gate import GateAtom
from fluss.engine.atoms.filter.all import AllAtom
from fluss.engine.rpc_contract import RPCContract
from .base import Atom
from .transport import AtomTransport
from rekuest.messages import Assign
from typing import Any, Optional
from fluss.engine.atoms.operations.math import MathAtom, operation_map
from rekuest.actors.base import Actor
from fluss.engine.reference_counter import ReferenceCounter


def atomify(
    node: BaseGraphNodeBase,
    transport: AtomTransport,
    contract: Optional[RPCContract],
    globals: Dict[str, Any],
    assignment: Assign,
    reference_counter: ReferenceCounter,
    actor: Actor = None,
) -> Atom:
    if isinstance(node, RekuestMapActionNode):
        if node.action_kind == ActionKind.FUNCTION:
            if node.map_strategy == MapStrategy.MAP:
                return ArkitektMapAtom(
                    node=node,
                    contract=contract,
                    transport=transport,
                    assignment=assignment,
                    globals=globals,
                    actor=actor,
                    reference_counter=reference_counter,
                )
            if node.map_strategy == MapStrategy.AS_COMPLETED:
                return ArkitektAsCompletedAtom(
                    node=node,
                    contract=contract,
                    transport=transport,
                    assignment=assignment,
                    globals=globals,
                    actor=actor,
                    reference_counter=reference_counter,
                )
            if node.map_strategy == MapStrategy.ORDERED:
                return ArkitektAsCompletedAtom(
                    node=node,
                    contract=contract,
                    transport=transport,
                    assignment=assignment,
                    globals=globals,
                    actor=actor,
                    reference_counter=reference_counter,
                )

            raise NotImplementedError(
                f"Map strategy {node.map_strategy} is not implemented"
            )
        if node.action_kind == ActionKind.GENERATOR:
            return ArkitektMergeMapAtom(
                node=node,
                contract=contract,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )

        raise NotImplementedError(f"Node kind {node.kind} is not implemented")
    if isinstance(node, RekuestFilterActionNode):
        if node.action_kind == ActionKind.FUNCTION:
            if node.map_strategy == MapStrategy.MAP:
                return ArkitektFilterAtom(
                    node=node,
                    contract=contract,
                    transport=transport,
                    assignment=assignment,
                    globals=globals,
                    actor=actor,
                    reference_counter=reference_counter,
                )
        if node.action_kind == ActionKind.GENERATOR:
            raise NotImplementedError("Generator cannot be used as a filter")

    if isinstance(node, ReactiveNode):
        if node.implementation == ReactiveImplementation.ZIP:
            return ZipAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.BUFFER_COUNT:
            return BufferCountAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.FILTER:
            return FilterAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.CHUNK:
            return ChunkAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.GATE:
            return GateAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.OMIT:
            return OmitAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )

        if node.implementation == ReactiveImplementation.BUFFER_COMPLETE:
            return BufferCompleteAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.WITHLATEST:
            return WithLatestAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.COMBINELATEST:
            return WithLatestAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.SPLIT:
            return SplitAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation == ReactiveImplementation.ALL:
            return AllAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )
        if node.implementation in operation_map:
            return MathAtom(
                node=node,
                transport=transport,
                assignment=assignment,
                globals=globals,
                actor=actor,
                reference_counter=reference_counter,
            )

    raise NotImplementedError(f"Atom for {node} {type(node)} is not implemented")
