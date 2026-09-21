"""A fluss call goes through the client it is made on, and nothing else.

No server: the rath is a fake returning canned data.
"""

from types import SimpleNamespace
from typing import Any, AsyncIterator, Optional

import pytest
from pydantic import BaseModel, ConfigDict
from rath.origin import ContextBound, get_origin

from fluss.fluss import Fluss


class FakeRath:
    """Answers every query with the same canned flow, and remembers what was sent."""

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def _answer(self, variables: dict[str, Any]) -> Any:
        self.sent.append(variables)
        return SimpleNamespace(data={"flow": {"id": "flow-1", "graph": {"id": "g-1"}}})

    async def aquery(self, document: str, variables: dict[str, Any]) -> Any:
        return self._answer(variables)

    async def asubscribe(self, document: str, variables: dict[str, Any]) -> AsyncIterator[Any]:
        yield self._answer(variables)


class Graph(ContextBound):
    model_config = ConfigDict(frozen=True)
    id: str


class Flow(ContextBound):
    model_config = ConfigDict(frozen=True)
    id: str
    graph: Graph


class GetFlow(BaseModel):
    """Shaped like a generated operation."""

    flow: Flow

    class Arguments(BaseModel):
        id: str
        note: Optional[str] = None

    class Meta:
        document = "query GetFlow($id: ID!) { flow(id: $id) { id graph { id } } }"


def client() -> Any:
    """The real client over a fake rath, built without validating the rath."""
    return Fluss.model_construct(rath=FakeRath())


@pytest.mark.asyncio
async def test_aexecute_goes_through_the_client_and_results_remember_it() -> None:
    mine, other = client(), client()

    result = await mine.aexecute(GetFlow, {"id": "flow-1"})

    assert (len(mine.rath.sent), len(other.rath.sent)) == (1, 0)
    origin = get_origin(result.flow.graph)
    assert origin is not None and origin.client is mine and origin.rath is mine.rath


def test_execute_goes_through_the_client() -> None:
    from koil import Koil

    mine = client()
    with Koil():
        assert mine.execute(GetFlow, {"id": "flow-1"}).flow.id == "flow-1"
    assert len(mine.rath.sent) == 1


@pytest.mark.asyncio
async def test_asubscribe_goes_through_the_client() -> None:
    mine = client()
    events = [e async for e in mine.asubscribe(GetFlow, {"id": "flow-1"})]
    assert [e.flow.id for e in events] == ["flow-1"]
    assert get_origin(events[0].flow).client is mine


@pytest.mark.asyncio
async def test_unset_arguments_are_still_sent() -> None:
    """fluss's wire behaviour, kept through the rewrite: no exclude_unset."""
    mine = client()
    await mine.aexecute(GetFlow, {"id": "flow-1"})
    assert mine.rath.sent == [{"id": "flow-1", "note": None}]


def test_run_flow_takes_its_clients_and_task_by_injection() -> None:
    """Only the flow and its kwargs are ports; fluss, rekuest and task are injected.

    A parameter is a client because a service on the registry returns its class,
    so this reads the registry fluss ships -- which takes rekuest's service in
    before it registers ``run_flow``.
    """
    from rekuest.actors.actify import derive_implementation_details
    from rekuest.rekuest import Rekuest

    from fluss.arkitekt import registry
    from fluss.engine.actions import run_flow
    from fluss.engine.rekuest import RUN_FLOW_CONFIG

    wanted = derive_implementation_details(
        run_flow, RUN_FLOW_CONFIG, registry.structure_registry
    ).injected_variables
    assert wanted.task_variables == ["task"]
    assert wanted.service_client_variables == {"fluss": Fluss, "rekuest": Rekuest}
