"""The combination atoms, and how atomify treats the map strategies it lacks.

COMBINELATEST used to build a WithLatestAtom, and WithLatestAtom constructed the
``OutEvent`` union itself, so neither ever emitted. atomify compared against
``MapStrategy.AS_COMPLETED``/``ORDERED``, which the schema no longer has, so any
strategy but MAP raised AttributeError instead of saying it is not implemented.
"""

import asyncio

import pytest

from fluss.api.schema import (
    ActionKind,
    MapStrategy,
    ReactiveImplementation,
    ReactiveNode,
    RekuestMapActionNode,
)
from fluss.engine.atoms.combination.combinelatest import CombineLatestAtom
from fluss.engine.atoms.combination.withlatest import WithLatestAtom
from fluss.engine.atoms.transport import MockTransport
from fluss.engine.atoms.utils import atomify
from fluss.engine.events import CompleteInEvent, EventType, NextInEvent, OutEvent
from fluss.engine.reference_counter import ReferenceCounter

from .utils import expectnext


def _next(handle: str, value: tuple, t: int) -> NextInEvent:
    return NextInEvent(target="1", handle=handle, value=value, current_t=t)


async def _nothing_within(transport: MockTransport, timeout: float = 0.2) -> bool:
    try:
        await transport.get(timeout=timeout)
    except asyncio.TimeoutError:
        return True
    return False


def _reactive(node: ReactiveNode, implementation: ReactiveImplementation) -> ReactiveNode:
    return node.model_copy(update={"implementation": implementation})


@pytest.mark.asyncio
async def test_combine_latest_emits_on_either_stream(reactive_zip_node: ReactiveNode):
    transport = MockTransport(queue=asyncio.Queue[OutEvent]())
    node = _reactive(reactive_zip_node, ReactiveImplementation.COMBINELATEST)

    async with CombineLatestAtom(
        node=node, transport=transport, reference_counter=ReferenceCounter()
    ) as atom:
        task = asyncio.create_task(atom.start())

        await atom.put(_next("arg_0", (1,), 0))
        assert await _nothing_within(transport), "waits for every stream"

        await atom.put(_next("arg_1", (10,), 1))
        assert expectnext(await transport.get(timeout=1)).value == (1, 10)

        await atom.put(_next("arg_1", (20,), 2))
        assert expectnext(await transport.get(timeout=1)).value == (1, 20)

        await atom.put(_next("arg_0", (2,), 3))
        assert expectnext(await transport.get(timeout=1)).value == (2, 20)

        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_with_latest_emits_only_on_the_first_stream(reactive_zip_node: ReactiveNode):
    transport = MockTransport(queue=asyncio.Queue[OutEvent]())
    node = _reactive(reactive_zip_node, ReactiveImplementation.WITHLATEST)

    async with WithLatestAtom(
        node=node, transport=transport, reference_counter=ReferenceCounter()
    ) as atom:
        task = asyncio.create_task(atom.start())

        await atom.put(_next("arg_1", (10,), 0))
        await atom.put(_next("arg_0", (1,), 1))
        assert expectnext(await transport.get(timeout=1)).value == (1, 10)

        await atom.put(_next("arg_1", (20,), 2))
        assert await _nothing_within(transport), "the second stream only updates"

        await atom.put(_next("arg_0", (2,), 3))
        assert expectnext(await transport.get(timeout=1)).value == (2, 20)

        await atom.put(CompleteInEvent(target="1", handle="arg_0", current_t=4))
        assert (await transport.get(timeout=1)).type == EventType.COMPLETE

        await asyncio.wait_for(task, timeout=1)


def _map_node(reactive_zip_node: ReactiveNode, strategy: MapStrategy) -> RekuestMapActionNode:
    return RekuestMapActionNode.model_construct(
        id="1",
        ins=reactive_zip_node.ins[:1],
        outs=reactive_zip_node.outs,
        constants_map={},
        map_strategy=strategy,
        action_kind=ActionKind.FUNCTION,
    )


def _atomify(node):
    return atomify(
        node,
        transport=MockTransport(queue=asyncio.Queue[OutEvent]()),
        contract=None,
        globals={},
        assignment=None,
        reference_counter=ReferenceCounter(),
    )


def test_combine_latest_and_with_latest_build_their_own_atoms(reactive_zip_node: ReactiveNode):
    combine = _reactive(reactive_zip_node, ReactiveImplementation.COMBINELATEST)
    with_latest = _reactive(reactive_zip_node, ReactiveImplementation.WITHLATEST)

    assert isinstance(_atomify(combine), CombineLatestAtom)
    assert isinstance(_atomify(with_latest), WithLatestAtom)


@pytest.mark.parametrize("strategy", [MapStrategy.MAP_TO, MapStrategy.MAP_FROM])
def test_an_unimplemented_map_strategy_says_so(reactive_zip_node: ReactiveNode, strategy):
    with pytest.raises(NotImplementedError, match="Map strategy"):
        _atomify(_map_node(reactive_zip_node, strategy))
