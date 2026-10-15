"""Store a Python flow version from its source, and deploy a published one as an action.

The fluss server validates what it stores (with fluss-monty, as the executor does): a client
sends the source and the actions it may call, with their ports, and the server derives the
flow's ports and runtime or refuses the source with its diagnostics. Check a source without
storing it with ``fluss.avalidate_python_flow`` (or locally, with
:func:`fluss_monty.validate_python_flow`).
"""

from typing import Any, Iterable, Mapping, Sequence

from arkitekt_spec.actions import ActionKind, ArgPortInput, DefinitionInput, ReturnPortInput
from fluss_monty import ManifestAction, PortLike
from rath.scalars import IDCoercible
from rekuest.api.schema import Implementation
from rekuest.client.client import Rekuest

from fluss.api import schema
from fluss.api.schema import Effects, ManifestEntryInput, PythonFlow, PythonFlowStatus
from fluss.fluss import Fluss


async def amanifest(actions: Mapping[str, str], rekuest: Rekuest, effects: Mapping[str, Effects] | None = None) -> list[ManifestAction]:
    """``{alias: action hash}`` as manifest actions, each looked up in rekuest.

    ``effects`` declares what calling each alias again would do to the world (undeclared is UNKNOWN): rekuest's ``Action`` does not
    carry its implementations' effects, so the author of the flow says so.
    """
    effects = effects or {}
    return [
        ManifestAction(alias=alias, action=await rekuest.afind(hash=hash), effect=effects.get(alias, Effects.UNKNOWN).value)
        for alias, hash in actions.items()
    ]


def _port(port: PortLike, cls: type[Any]) -> Any:  # noqa: ANN401 -- a fluss ArgPortInput or ReturnPortInput, as ``cls``
    """What validation reads of a port (its type, not its widgets or effects), as a fluss port input."""
    fields: dict[str, Any] = {"key": port.key, "kind": getattr(port.kind, "value", port.kind), "nullable": bool(port.nullable)}
    if getattr(port, "identifier", None):
        fields["identifier"] = port.identifier
    default = getattr(port, "default", None)
    if cls is schema.ArgPortInput and default is not None:
        fields["default"] = default
    children = getattr(port, "children", None)
    if children:
        fields["children"] = tuple(_port(child, cls) for child in children)
    return cls(**fields)


def manifest_inputs(actions: Sequence[ManifestAction]) -> list[ManifestEntryInput]:
    """The manifest as the server takes it: each action by its hash, with the ports the source is checked against."""
    return [
        ManifestEntryInput(
            alias=entry.alias,
            action_hash=str(entry.action.hash),
            kind=schema.ActionKind(str(getattr(entry.action.kind, "value", entry.action.kind))),
            args=tuple(_port(port, schema.ArgPortInput) for port in entry.action.args),
            returns=tuple(_port(port, schema.ReturnPortInput) for port in entry.action.returns),
            effect=Effects(entry.effect),
            app=entry.app,
            key=entry.key,
            version=entry.version,
        )
        for entry in actions
    ]


async def acreate_python_flow_from_source(
    source: str,
    actions: Sequence[ManifestAction],
    fluss: Fluss,
    *,
    title: str | None = None,
    description: str | None = None,
    previous: str | None = None,
    entrypoint: str = "main",
    structures: Iterable[str] = (),
    publish: bool = False,
) -> PythonFlow:
    """Store ``source`` as a DRAFT (or published) version; the server refuses one that does not validate."""
    flow = await fluss.acreate_python_flow(
        source=source,
        entrypoint=entrypoint,
        manifest=manifest_inputs(actions),
        structures=list(structures),
        title=title,
        description=description,
        previous=previous,
    )
    if publish:
        flow = await fluss.apublish_python_flow(id=flow.id)
    return flow


def python_flow_definition(flow: PythonFlow) -> DefinitionInput:
    """The action a published version is: its own ports, as a FUNCTION."""
    return DefinitionInput(
        name=flow.title,
        key=f"pythonflow_{flow.id}",
        version="1",
        kind=ActionKind.FUNCTION,
        description=flow.description or f"The Python flow {flow.title}",
        args=tuple(ArgPortInput.model_validate(port.model_dump(by_alias=True, exclude_none=True)) for port in flow.args),
        returns=tuple(ReturnPortInput.model_validate(port.model_dump(by_alias=True, exclude_none=True)) for port in flow.returns),
        stateful=False,
        is_dev=False,
        collections=(),
        port_groups=(),
        is_test_for=(),
    )


async def adeploy_python_flow(flow: PythonFlow, rekuest: Rekuest, runner: IDCoercible) -> Implementation:
    """Make a PUBLISHED version callable like any action, on the agent of ``runner``.

    ``runner`` is a ``run_python_flow`` implementation. The action rekuest makes of it takes the
    flow's own arguments and returns its own values: rekuest binds the version, packs the
    arguments into ``kwargs`` and unpacks ``returns`` (``returns_key``). Deploying again
    redeploys the same interface.
    """
    if flow.status != PythonFlowStatus.PUBLISHED:
        raise ValueError(f"Only a PUBLISHED Python flow is deployed; {flow.id} is {flow.status.value}")
    return await rekuest.acreate_higher_order_implementation(
        lower=runner,
        interface=f"pythonflow:{flow.id}",
        definition=python_flow_definition(flow),
        config={"bound": {"flow": str(flow.id)}, "args_key": "kwargs", "returns_key": "returns"},
    )
