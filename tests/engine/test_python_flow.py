"""The rekuest side of Python flows: the run_python_flow action, its actor, stored flows, deploying.

The sandbox itself is fluss-monty's (and tested there); here fluss, rekuest and the task are
fakes behind the action, and Monty is real.
"""

import ast
import asyncio
import time
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio

pytest.importorskip("fluss_monty")
import pydantic_monty  # noqa: E402

from fluss.api.schema import ArgPortInput, Effects, PortKind, ReturnPortInput  # noqa: E402
from fluss_monty import ManifestAction, arun_python_flow, build_stubs, validate_python_flow  # noqa: E402

def arg(key: str, kind: PortKind, **extra: Any) -> ArgPortInput:
    return ArgPortInput(key=key, kind=kind, nullable=extra.pop("nullable", False), **extra)


def ret(key: str, kind: PortKind, **extra: Any) -> ReturnPortInput:
    return ReturnPortInput(key=key, kind=kind, nullable=extra.pop("nullable", False), **extra)


IMAGE = "@mikro/image"


def action(hash: str, args: list, returns: list, kind: str = "FUNCTION") -> SimpleNamespace:
    return SimpleNamespace(hash=hash, kind=kind, args=args, returns=returns)


SEGMENT = ManifestAction(
    alias="segment",
    action=action("h-seg", [arg("image", PortKind.STRUCTURE, identifier=IMAGE), arg("sigma", PortKind.FLOAT, nullable=True)], [ret("return0", PortKind.STRUCTURE, identifier=IMAGE)]),
)
MEASURE = ManifestAction(
    alias="measure",
    action=action("h-measure", [arg("image", PortKind.STRUCTURE, identifier=IMAGE)], [ret("count", PortKind.INT), ret("area", PortKind.FLOAT)]),
)
MOVE = ManifestAction(alias="move_stage", action=action("h-move", [arg("x", PortKind.FLOAT)], []), effect=Effects.IRREVERSIBLE)
ACTIONS = [SEGMENT, MEASURE, MOVE]

SOURCE = '''"""Segment an image and count what is in it."""

import asyncio

THRESHOLD = 3


async def main(image: MikroImage, repeats: int = 1) -> tuple[MikroImage, int]:
    masks = await asyncio.gather(*[segment(image, sigma=1.5) for _ in range(repeats)])
    count, area = await measure(masks[0])
    print("counted", count, "over", area)
    return masks[0], count
'''


class Recorder:
    """The injected caller: records every call, answers from ``impls``."""

    def __init__(self, delay: float = 0.0) -> None:
        self.calls: list[tuple[str, dict, str]] = []
        self.delay = delay

    async def __call__(self, entry: ManifestAction, kwargs: dict, call_key: str) -> dict:
        self.calls.append((entry.alias, kwargs, call_key))
        await asyncio.sleep(self.delay)
        if entry.alias == "segment":
            if kwargs["image"] == "broken":
                raise RuntimeError("the segmenter crashed")
            return {"return0": f"{kwargs['image']}-mask"}
        if entry.alias == "measure":
            return {"count": 7, "area": 12.5}
        return {}


@pytest_asyncio.fixture
async def pool():
    async with pydantic_monty.AsyncMonty(min_processes=1, max_processes=2) as pool:
        yield pool


# --- rekuest wiring ----------------------------------------------------------------------


def test_run_python_flow_is_registered_with_a_handcrafted_definition() -> None:
    from arkitekt_spec.declare.actors.actify import derive_implementation_details
    from rekuest.client.client import Rekuest

    from fluss.arkitekt import registry
    from fluss.engine.python.actions import PythonFlowActor, build_run_python_flow_definition, python_flow_actifier, run_python_flow
    from fluss.engine.rekuest import RUN_PYTHON_FLOW_CONFIG
    from fluss.fluss import Fluss

    wanted = derive_implementation_details(run_python_flow, RUN_PYTHON_FLOW_CONFIG, registry.structure_registry).injected_variables
    assert wanted.task_variables == ["task"]
    assert wanted.service_client_variables == {"fluss": Fluss, "rekuest": Rekuest}

    definition = build_run_python_flow_definition(registry.structure_registry)
    assert [(p.key, p.kind, p.identifier) for p in definition.args] == [("flow", "STRUCTURE", "@fluss/pythonflow"), ("kwargs", "DICT", None)]
    assert definition.kind == "FUNCTION"

    # One actor serves every run, and owns the worker pool they share.
    _, _, builder = python_flow_actifier(run_python_flow, registry.structure_registry, RUN_PYTHON_FLOW_CONFIG)
    assert builder.func is PythonFlowActor


# --- the shapes production feeds in ------------------------------------------------------


def _deep_list(depth: int) -> dict:
    port: dict = {"key": "...", "kind": "INT", "nullable": False}
    for _ in range(depth):
        port = {"__typename": "ArgPort", "key": "...", "kind": "LIST", "nullable": False, "children": [port]}
    return {**port, "key": "xs"}


def test_a_real_action_with_ports_deeper_than_its_fragment_stubs_loosely() -> None:
    """rekuest's ``Action`` fragment stops nesting; the missing depth is typed ``Any``, not a crash."""
    from rekuest.api.schema import Action

    real = Action.model_validate(
        {
            "__typename": "Action", "hash": "h-deep", "id": "1", "name": "deep", "kind": "FUNCTION", "description": None,
            "args": [_deep_list(4)],
            "returns": [{"__typename": "ReturnPort", "key": "return0", "kind": "STRUCTURE", "identifier": IMAGE, "nullable": False}],
            "collections": [], "isDev": False, "isTestFor": [], "portGroups": [], "stateful": False,
        }
    )
    stubs, classes = build_stubs([ManifestAction(alias="deep", action=real)])
    assert "async def deep(xs: list[list[list[Any]]]) -> MikroImage: ..." in stubs
    assert classes == {"MikroImage": IMAGE}


@pytest.mark.asyncio
async def test_a_run_from_a_stored_fluss_python_flow(pool) -> None:
    """The runner reads a ``PythonFlow`` as the server returns it, and derives its ports again."""
    from fluss.api.schema import PythonFlow

    report = await validate_python_flow(SOURCE, ACTIONS, pool=pool)
    stored = PythonFlow.model_validate(
        {
            "__typename": "PythonFlow", "id": "1", "title": "t", "lineage": "l", "source": SOURCE, "entrypoint": "main",
            "runtime": report.runtime, "status": "PUBLISHED", "hash": "h", "physical": False, "createdAt": "2026-09-28T00:00:00Z",
            "args": [{"__typename": "ArgPort", **p.model_dump(by_alias=True, exclude_none=True)} for p in report.args],
            "returns": [{"__typename": "ReturnPort", **p.model_dump(by_alias=True, exclude_none=True)} for p in report.returns],
            "manifest": [{"__typename": "ManifestEntry", "actionHash": m.action_hash, **m.model_dump(exclude={"action_hash"})} for m in report.manifest],
        }
    )
    returns = await arun_python_flow(stored.source, {"image": "img"}, ACTIONS, Recorder(), args=stored.args, returns=stored.returns, pool=pool)
    assert returns == {"return0": "img-mask", "return1": 7}


# --- run_python_flow, against fake fluss/rekuest/task --------------------------------------


class FakeTask:
    def __init__(self, block: bool = False) -> None:
        self.id = "task-1"
        self.logs: list[tuple[str, Any]] = []
        self.keys: list[str] = []
        self.logged_before_call: list[list[str]] = []
        self.block = block
        self.cancelled = False
        self.references: list[str] = []

    async def acall_raw(self, *, kwargs: dict, action: Any, reference: str, call_key: str) -> dict:  # noqa: ANN401
        self.keys.append(call_key)
        self.references.append(reference)
        await asyncio.sleep(0.05)
        self.logged_before_call.append([text for text, _ in self.logs])
        if self.block:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        return {"return0": f"{kwargs['image']}-mask"}

    async def alog(self, text: str, level: Any) -> None:  # noqa: ANN401
        self.logs.append((text, level))


class FakeFluss:
    def __init__(self, flow: Any) -> None:  # noqa: ANN401
        self.flow = flow
        self.closed: list[str] = []

    async def aget_python_flow(self, id: str) -> Any:  # noqa: ANN401
        return self.flow

    async def acreate_python_run(self, flow: str, task_id: str) -> Any:  # noqa: ANN401
        import datetime

        return SimpleNamespace(id="run-1", created_at=datetime.datetime(2026, 10, 15, tzinfo=datetime.timezone.utc))

    async def aclose_python_run(self, run: str, status: Any) -> None:  # noqa: ANN401
        self.closed.append(status.value)


class FakeRekuest:
    async def afind(self, hash: str) -> Any:  # noqa: ANN401
        return SEGMENT.action


LOGGING = "async def main(image: MikroImage) -> MikroImage:\n    print('segmenting', image)\n    return await segment(image)\n"


async def _stored(pool, source: str) -> Any:  # noqa: ANN401
    from fluss.api.schema import PythonFlow

    report = await validate_python_flow(source, [SEGMENT], pool=pool)
    assert report.ok, report.diagnostics
    return PythonFlow.model_validate(
        {
            "__typename": "PythonFlow", "id": "1", "title": "t", "lineage": "l", "source": source, "entrypoint": "main",
            "runtime": report.runtime, "status": "PUBLISHED", "hash": "h", "physical": False, "createdAt": "2026-09-28T00:00:00Z",
            "args": [{"__typename": "ArgPort", **p.model_dump(by_alias=True, exclude_none=True)} for p in report.args],
            "returns": [{"__typename": "ReturnPort", **p.model_dump(by_alias=True, exclude_none=True)} for p in report.returns],
            "manifest": [{"__typename": "ManifestEntry", "actionHash": m.action_hash, **m.model_dump(exclude={"action_hash"})} for m in report.manifest],
        }
    )


@pytest.mark.asyncio
async def test_run_python_flow_logs_while_it_runs_and_keys_its_calls(pool) -> None:
    from fluss.engine.python.actions import MontyPool, run_python_flow

    flow, task, monty = FakeFluss(await _stored(pool, LOGGING)), FakeTask(), MontyPool(max_processes=1)
    try:
        returns = await run_python_flow("1", {"image": "img"}, flow, FakeRekuest(), task, pool=monty)  # type: ignore[arg-type]
        first = await monty.aget()
        await run_python_flow("1", {"image": "img"}, flow, FakeRekuest(), task, pool=monty)  # type: ignore[arg-type]
        assert await monty.aget() is first
    finally:
        await monty.aclose()
    assert returns == {"return0": "img-mask"}
    assert task.logged_before_call[0] == ["segmenting img"]
    assert task.keys[0] == task.keys[1] and task.keys[0].startswith("segment:")
    # The reference rekuest falls back on names the call itself, never just its action.
    assert task.references[0] == f"task-1:{task.keys[0]}"
    assert flow.closed == ["COMPLETED", "COMPLETED"]


@pytest.mark.asyncio
async def test_a_cancelled_run_is_closed_cancelled(pool) -> None:
    from fluss.engine.python.actions import run_python_flow

    flow, task = FakeFluss(await _stored(pool, LOGGING)), FakeTask(block=True)
    running = asyncio.create_task(run_python_flow("1", {"image": "img"}, flow, FakeRekuest(), task))  # type: ignore[arg-type]
    while not task.logged_before_call:
        await asyncio.sleep(0.05)
    running.cancel()
    with pytest.raises(asyncio.CancelledError):
        await running
    assert flow.closed == ["CANCELLED"]
    assert task.cancelled, "the call in flight is cancelled with its run"
    assert [text for text, _ in task.logs] == ["segmenting img"]


# --- deploying a published version as an action ------------------------------------------


@pytest.mark.asyncio
async def test_a_published_version_deploys_as_a_wrapper_of_run_python_flow(pool) -> None:
    from fluss.engine.python.client import adeploy_python_flow

    class Deployer:
        async def acreate_higher_order_implementation(self, **kwargs: Any) -> dict:  # noqa: ANN401
            self.kwargs = kwargs
            return kwargs

    flow, rekuest = await _stored(pool, LOGGING), Deployer()
    await adeploy_python_flow(flow, rekuest, runner="impl-7")  # type: ignore[arg-type]
    sent = rekuest.kwargs
    assert (sent["lower"], sent["interface"]) == ("impl-7", "pythonflow:1")
    assert sent["config"] == {"bound": {"flow": "1"}, "args_key": "kwargs", "returns_key": "returns"}
    definition = sent["definition"]
    assert definition.kind == "FUNCTION"
    assert [(p.key, p.kind, p.identifier) for p in definition.args] == [("image", "STRUCTURE", IMAGE)]
    assert [(p.key, p.kind, p.identifier) for p in definition.returns] == [("return0", "STRUCTURE", IMAGE)]

    from fluss.api.schema import PythonFlowStatus

    draft = flow.model_copy(update={"status": PythonFlowStatus.DRAFT})
    with pytest.raises(ValueError, match="PUBLISHED"):
        await adeploy_python_flow(draft, rekuest, runner="impl-7")  # type: ignore[arg-type]


# --- what the server is sent ---------------------------------------------------------------


def test_the_manifest_sent_carries_each_actions_typed_ports_and_nothing_else() -> None:
    """The server checks the source against these ports; widgets and effects are not its concern."""
    from rekuest.api.schema import Action

    from fluss.engine.python.client import manifest_inputs

    real = Action.model_validate(
        {
            "__typename": "Action", "hash": "h-seg", "id": "1", "name": "segment", "kind": "FUNCTION", "description": None,
            "args": [
                {"__typename": "ArgPort", "key": "image", "kind": "STRUCTURE", "identifier": IMAGE, "nullable": False, "label": "Image", "description": "The input"},
                {"__typename": "ArgPort", "key": "sigma", "kind": "FLOAT", "nullable": True, "default": 1.5},
                _deep_list(2),
            ],
            "returns": [{"__typename": "ReturnPort", "key": "return0", "kind": "STRUCTURE", "identifier": IMAGE, "nullable": False}],
            "collections": [], "isDev": False, "isTestFor": [], "portGroups": [], "stateful": False,
        }
    )
    [sent] = manifest_inputs([ManifestAction(alias="segment", action=real, effect="IRREVERSIBLE")])
    wire = sent.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert (wire["alias"], wire["actionHash"], wire["kind"], wire["effect"]) == ("segment", "h-seg", "FUNCTION", "IRREVERSIBLE")
    assert wire["args"][0] == {"key": "image", "kind": "STRUCTURE", "identifier": IMAGE, "nullable": False}
    assert wire["args"][1] == {"key": "sigma", "kind": "FLOAT", "nullable": True, "default": 1.5}
    assert wire["args"][2]["children"][0]["kind"] == "LIST"
    assert wire["returns"] == [{"key": "return0", "kind": "STRUCTURE", "identifier": IMAGE, "nullable": False}]


@pytest.mark.asyncio
async def test_storing_a_source_sends_it_with_its_manifest_and_publishes_on_request() -> None:
    from fluss.engine.python.client import acreate_python_flow_from_source

    class Recording:
        async def acreate_python_flow(self, **kwargs: Any) -> Any:  # noqa: ANN401
            self.created = kwargs
            return SimpleNamespace(id="7")

        async def apublish_python_flow(self, id: str) -> Any:  # noqa: ANN401
            self.published = id
            return SimpleNamespace(id=id, status="PUBLISHED")

    fluss = Recording()
    flow = await acreate_python_flow_from_source(LOGGING, [SEGMENT], fluss, title="Segment", publish=True)  # type: ignore[arg-type]
    assert (flow.id, fluss.published) == ("7", "7")
    assert set(fluss.created) == {"source", "entrypoint", "manifest", "structures", "title", "description", "previous"}
    assert [entry.alias for entry in fluss.created["manifest"]] == ["segment"]


@pytest.mark.asyncio
async def test_the_actor_hands_every_run_its_pool_and_closes_it_with_itself() -> None:
    from fluss.engine.python.actions import MontyPool, PythonFlowActor

    seen: list[Any] = []

    async def assign(**params: Any) -> dict:  # noqa: ANN401
        seen.append(params["pool"])
        await params["pool"].aget()
        return {}

    actor = PythonFlowActor.model_construct(assign=assign, iterator=lambda function, **params: _once(function, **params))
    actor._pool = MontyPool(max_processes=1)
    for _ in range(2):
        async for _ in actor.aiterate_results(flow="1"):
            pass
    assert seen[0] is seen[1] is actor._pool
    assert actor._pool._pool is not None

    async def no_runs(*args: Any, **kwargs: Any) -> int:  # noqa: ANN401
        return 0

    actor._astop_all = no_runs  # type: ignore[method-assign]
    await actor.acancel()
    assert actor._pool._pool is None


async def _once(function: Any, **params: Any) -> Any:  # noqa: ANN401
    yield await function(**params)
