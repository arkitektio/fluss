"""The generic ``run_python_flow`` action: runs any published Python flow version.

Like ``run_flow``, its definition is handcrafted (:func:`python_flow_actifier`): the flow's own
arguments arrive as one server-validated ``kwargs`` dict and leave as one ``returns`` dict, so
the actor neither expands nor shrinks -- the flow computes on raw wire values (structure IDs).
Each action the flow calls is a child task of the run.
"""

from functools import partial
from typing import Any, Dict, Optional, Tuple

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
from fluss.engine.python.manifest import ManifestAction
from fluss.engine.python.runner import PythonFlowError, PythonFlowLimits, arun_python_flow
from fluss.fluss import Fluss


async def resolve_manifest(flow: PythonFlow, rekuest: Rekuest) -> dict[str, tuple[ManifestAction, Action]]:
    """The flow's manifest with each action looked up by its hash: a missing one fails the run up front."""
    resolved: dict[str, tuple[ManifestAction, Action]] = {}
    for entry in flow.manifest:
        action = await rekuest.afind(hash=entry.action_hash)
        manifest_action = ManifestAction(alias=entry.alias, action=action, effect=entry.effect, app=entry.app, key=entry.key, version=entry.version)
        resolved[entry.alias] = (manifest_action, action)
    return resolved


async def run_python_flow(
    flow: str,
    kwargs: Dict[str, Any],
    fluss: Fluss,
    rekuest: Rekuest,
    task: Task,
) -> Dict[str, Any]:
    """Run Python Flow

    Runs a published Python flow version with pre-validated, shrunk argument values keyed by
    its arg ports, returning raw values keyed by its return ports.
    """
    # Inputs arrive unexpanded (bypass_expand), so the flow port is a raw ID.
    resolved = await fluss.aget_python_flow(id=ID.validate(flow))
    if resolved.status != PythonFlowStatus.PUBLISHED:
        raise PythonFlowError(f"Python flow {resolved.id} is {resolved.status.value}; only a PUBLISHED version runs")

    run = await fluss.acreate_python_run(flow=resolved.id, task_id=task.id)
    output: list[str] = []
    status = PythonRunStatus.FAILED
    try:
        actions = await resolve_manifest(resolved, rekuest)

        async def call(entry: ManifestAction, arguments: Dict[str, Any], reference: str) -> Dict[str, Any] | None:
            return await task.acall_raw(kwargs=arguments, action=actions[entry.alias][1], reference=reference)

        returns = await arun_python_flow(
            resolved.source,
            kwargs or {},
            [manifest_action for manifest_action, _ in actions.values()],
            call,
            entrypoint=resolved.entrypoint,
            args=resolved.args,
            returns=resolved.returns,
            limits=PythonFlowLimits(),
            print_callback=lambda stream, text: output.append(text),
        )
        status = PythonRunStatus.COMPLETED
        return returns
    except PythonFlowError as error:
        if error.traceback:
            await task.alog(error.traceback, LogLevel.ERROR)
        raise
    finally:
        if output:
            await task.alog("".join(output).rstrip("\n"), LogLevel.INFO)
        await fluss.aclose_python_run(run=run.id, status=status)


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
        isDev=False,
        collections=(),
        portGroups=(),
        isTestFor=(),
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
            FunctionalActor,
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
