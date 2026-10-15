"""The generic ``run_python_flow`` action: runs any published Python flow version.

Like ``run_flow``, its definition is handcrafted (:func:`python_flow_actifier`): the flow's own
arguments arrive as one server-validated ``kwargs`` dict and leave as one ``returns`` dict, so
the actor neither expands nor shrinks -- the flow computes on raw wire values (structure IDs).
Each action the flow calls is a child task of the run, keyed so a resumed run finds it again.

Its actor owns one Monty worker pool for every run it serves, started on the first run and
closed when the agent cancels the actor.
"""

import asyncio
import contextlib
from functools import partial
from typing import Any, AsyncGenerator, Dict, Optional, Self, Tuple

import pydantic_monty
from pydantic import PrivateAttr
from rath.scalars import ID
from arkitekt_runtime.actors.functional import FUNC, FunctionalActor
from arkitekt_runtime.actors.types import ActorBuilder
from arkitekt_runtime.task import Task
from arkitekt_spec.actions import ActionKind, ArgPortInput, DefinitionInput, PortKind, ReturnPortInput
from arkitekt_spec.declare.actors.actify import derive_implementation_details
from arkitekt_spec.declare.actors.types import ImplementationDetails, RegisterConfig
from arkitekt_spec.declare.protocol.types import AnyFunction
from arkitekt_spec.declare.structures.registry import StructureRegistry
from arkitekt_spec.declare.task import LogLevel
from rekuest.api.schema import Action
from rekuest.client.client import Rekuest

from fluss.api.schema import PythonFlow, PythonFlowStatus, PythonRunStatus
from fluss_monty import ManifestAction, PythonFlowError, PythonFlowLimits, arun_python_flow
from fluss.fluss import Fluss


class MontyPool:
    """One Monty worker pool, started on first use, until :meth:`aclose`."""

    def __init__(self, max_processes: int = 4) -> None:
        """Runs beyond ``max_processes`` wait for a free worker."""
        self.max_processes = max_processes
        self._pool: pydantic_monty.AsyncMonty | None = None
        self._lock = asyncio.Lock()

    async def aget(self) -> pydantic_monty.AsyncMonty:
        """The running pool."""
        async with self._lock:
            if self._pool is None:
                pool = pydantic_monty.AsyncMonty(min_processes=1, max_processes=self.max_processes)
                await pool.__aenter__()
                self._pool = pool
            return self._pool

    async def aclose(self) -> None:
        """Stop the workers; the next :meth:`aget` starts new ones."""
        async with self._lock:
            pool, self._pool = self._pool, None
            if pool is not None:
                await pool.__aexit__(None, None, None)


class PythonFlowActor(FunctionalActor):
    """The ``run_python_flow`` actor: hands every run its pool, and closes it with itself."""

    _pool: MontyPool = PrivateAttr(default_factory=MontyPool)

    def aiterate_results(self: Self, **params: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401 -- the run's params
        """Run the flow with the actor's pool."""
        return self.iterator(self.assign, pool=self._pool, **params)

    async def acancel(self: Self) -> None:
        """Cancel the runs, then stop the workers."""
        try:
            await super().acancel()
        finally:
            await self._pool.aclose()


class _LiveLog:
    """The sandbox's ``print`` output as task logs, while the run goes on.

    Monty may call back from a worker thread, so lines reach the loop through
    ``call_soon_threadsafe``; one drain task sends them in order.
    """

    def __init__(self, task: Task) -> None:
        self.task = task
        self.loop = asyncio.get_running_loop()
        self.queue: asyncio.Queue[tuple[str, str] | None] = asyncio.Queue()
        self.drain = asyncio.create_task(self._adrain())

    def __call__(self, stream: str, text: str) -> None:
        self.loop.call_soon_threadsafe(self.queue.put_nowait, (stream, text))

    async def _adrain(self) -> None:
        while (item := await self.queue.get()) is not None:
            stream, text = item
            if text := text.rstrip("\n"):
                await self.task.alog(text, LogLevel.WARN if stream == "stderr" else LogLevel.INFO)

    async def aclose(self) -> None:
        """Send what is still queued, then stop."""
        self.queue.put_nowait(None)
        await self.drain


async def resolve_manifest(flow: PythonFlow, rekuest: Rekuest) -> dict[str, tuple[ManifestAction, Action]]:
    """The flow's manifest with each action looked up by its hash: a missing one fails the run up front."""
    resolved: dict[str, tuple[ManifestAction, Action]] = {}
    for entry in flow.manifest:
        action = await rekuest.afind(hash=entry.action_hash)
        manifest_action = ManifestAction(alias=entry.alias, action=action, effect=entry.effect.value, app=entry.app, key=entry.key, version=entry.version)
        resolved[entry.alias] = (manifest_action, action)
    return resolved


async def run_python_flow(
    flow: str,
    kwargs: Dict[str, Any],
    fluss: Fluss,
    rekuest: Rekuest,
    task: Task,
    pool: MontyPool | None = None,
) -> Dict[str, Any]:
    """Run Python Flow

    Runs a published Python flow version with pre-validated, shrunk argument values keyed by
    its arg ports, returning raw values keyed by its return ports.
    """
    # Inputs arrive unexpanded (bypass_expand), so the flow port is a raw ID.
    resolved = await fluss.aget_python_flow(id=ID.validate(flow))
    if resolved.status != PythonFlowStatus.PUBLISHED:
        raise PythonFlowError(f"Python flow {resolved.id} is {resolved.status.value}; only a PUBLISHED version runs")

    # A resumed task gets its run again (one per task), and with it the seed the first attempt
    # drew from: the same flow makes the same calls, which find their results. The clock is
    # left running -- a frozen one would freeze `monotonic()` too, and every deadline with it.
    run = await fluss.acreate_python_run(flow=resolved.id, task_id=task.id)
    os_policy: pydantic_monty.OSPolicy = {"random_start": {"seed": f"{run.id}:{task.id}"}}
    log = _LiveLog(task)
    status = PythonRunStatus.FAILED
    try:
        actions = await resolve_manifest(resolved, rekuest)

        # rekuest finds a call again by its key, and failing that by its reference: so the
        # reference names this one call too (a bare alias would answer a call with another's).
        async def call(entry: ManifestAction, arguments: Dict[str, Any], call_key: str) -> Dict[str, Any] | None:
            return await task.acall_raw(kwargs=arguments, action=actions[entry.alias][1], reference=f"{task.id}:{call_key}", call_key=call_key)

        returns = await arun_python_flow(
            resolved.source,
            kwargs or {},
            [manifest_action for manifest_action, _ in actions.values()],
            call,
            entrypoint=resolved.entrypoint,
            args=resolved.args,
            returns=resolved.returns,
            pool=await pool.aget() if pool is not None else None,
            limits=PythonFlowLimits(),
            print_callback=log,
            os_policy=os_policy,
        )
        status = PythonRunStatus.COMPLETED
        return returns
    except asyncio.CancelledError:
        status = PythonRunStatus.CANCELLED
        raise
    except PythonFlowError as error:
        if error.traceback:
            await task.alog(error.traceback, LogLevel.ERROR)
        raise
    finally:
        # Shielded: a cancelled run is still closed, never left RUNNING.
        await asyncio.shield(_aclose(fluss, run.id, status, log))


async def _aclose(fluss: Fluss, run: ID, status: PythonRunStatus, log: _LiveLog) -> None:
    with contextlib.suppress(Exception):
        await log.aclose()
    await fluss.aclose_python_run(run=run, status=status)


def build_run_python_flow_definition(structure_registry: StructureRegistry) -> DefinitionInput:
    """The handcrafted definition of ``run_python_flow``."""
    flow_port = structure_registry.get_argport_for_cls(PythonFlow, "flow", nullable=False, description="The published Python flow version to run")

    # The DICT child kind is a placeholder: values are validated by the server's
    # higher-order implementation against the flow's own ports, never against this one.
    kwargs_port = ArgPortInput(
        key="kwargs",
        kind=PortKind.DICT,
        nullable=False,
        description="Shrunk values keyed by the flow's arg port keys, validated by the server",
        children=(ArgPortInput(key="...", kind=PortKind.STRING, nullable=True),),
    )
    returns_port = ReturnPortInput(
        key="returns",
        kind=PortKind.DICT,
        nullable=False,
        description="Raw values keyed by the flow's return port keys",
        children=(ReturnPortInput(key="...", kind=PortKind.STRING, nullable=True),),
    )

    return DefinitionInput(
        name="Run Python Flow",
        key="run_python_flow",
        version="1",
        kind=ActionKind.FUNCTION,
        description="Runs a published fluss Python flow in a Monty sandbox, as a generic higher-order executor",
        args=(flow_port, kwargs_port),
        returns=(returns_port,),
        stateful=False,
        is_dev=False,
        collections=(),
        port_groups=(),
        is_test_for=(),
    )


def python_flow_actifier(
    function: AnyFunction,
    structure_registry: StructureRegistry,
    config: Optional[RegisterConfig] = None,
) -> Tuple[DefinitionInput, ImplementationDetails, ActorBuilder]:
    """Like ``flow_actifier``, for the one-shot ``run_python_flow``."""
    config = config or RegisterConfig()
    implementation_details = derive_implementation_details(function, config, structure_registry)
    definition = build_run_python_flow_definition(structure_registry)
    return (
        definition,
        implementation_details,
        partial(
            PythonFlowActor,
            iterator=FUNC,
            assign=function,
            expand_inputs=False,
            shrink_outputs=False,
            structure_registry=structure_registry,
            definition=definition,
            **implementation_details.actor_kwargs(),
            concurrency=config.concurrency,
        ),
    )
