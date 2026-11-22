"""Deploy a graph flow as an action of its own, on the agent of a ``run_flow`` runner.

``run_flow`` runs any flow it is handed. A deployed flow is a wrapper of it (a higher-order
implementation) with the flow bound: an action that takes the flow's own arguments and yields
its own returns, and that says which agents its stateful steps run on when it is started.
"""

from arkitekt_spec.actions import (
    ActionKind,
    AgentDependencyInput,
    ArgPortInput,
    DefinitionInput,
    ReturnPortInput,
)
from rath.scalars import IDCoercible
from rekuest.api.schema import Implementation
from rekuest.client.client import Rekuest

from fluss.api.schema import ArgNode, Flow, RekuestActionNodeBase, ReturnNode
from fluss.engine.steps import step_dependency, step_key


def _as_arg(port: object) -> ArgPortInput:
    """A port of the flow as an argument of the action: fluss's ports are rekuest's, by field."""
    return ArgPortInput.model_validate(_fields(port, ArgPortInput))


def _as_return(port: object) -> ReturnPortInput:
    return ReturnPortInput.model_validate(_fields(port, ReturnPortInput))


def _fields(
    port: object, model: type[ArgPortInput] | type[ReturnPortInput]
) -> dict[str, object]:
    """What ``port`` says that ``model`` has a field for; its children the same way.

    A flow's argument node hands its values out (return ports) and its return node takes them
    in (argument ports): each is the other direction of what the action declares, so the
    fields the two directions do not share are left behind.
    """
    dumped = port.model_dump(by_alias=False, exclude_none=True)  # type: ignore[attr-defined]
    kept = {
        key: value
        for key, value in dumped.items()
        if key in model.model_fields and key != "children"
    }
    children = getattr(port, "children", None)
    if children:
        kept["children"] = tuple(
            model.model_validate(_fields(child, model)) for child in children
        )
    return kept


def flow_definition(flow: Flow) -> DefinitionInput:
    """The action a deployed flow is: its argument node's stream and its globals in, its return node's stream out.

    A GENERATOR, as ``run_flow`` is: a flow yields whenever a value reaches its return node.
    """
    # A flow without one of the two takes nothing, or yields nothing.
    arg_node = next(
        (node for node in flow.graph.nodes if isinstance(node, ArgNode)), None
    )
    return_node = next(
        (node for node in flow.graph.nodes if isinstance(node, ReturnNode)), None
    )
    taken = arg_node.outs[0] if arg_node is not None and arg_node.outs else ()
    yielded = return_node.ins[0] if return_node is not None and return_node.ins else ()
    return DefinitionInput(
        name=flow.title,
        key=f"flow_{flow.id}",
        version="1",
        kind=ActionKind.GENERATOR,
        description=getattr(flow, "description", None) or f"The flow {flow.title}",
        args=(
            *(_as_arg(port) for port in taken),
            *(_as_arg(entry.port) for entry in flow.graph.globals),
        ),
        returns=tuple(_as_return(port) for port in yielded),
        stateful=False,
        is_dev=False,
        collections=(),
        port_groups=(),
        is_test_for=(),
    )


async def flow_stateful_steps(
    flow: Flow, rekuest: Rekuest
) -> tuple[AgentDependencyInput, ...]:
    """What a deployed flow declares of its stateful steps: one dependency per such node.

    Per node, not per action: two nodes that call the same stateful action are two steps, and
    may be bound to two agents. Stateless nodes are not declared: they run wherever the action
    is offered.
    """
    steps: list[AgentDependencyInput] = []
    for node in flow.graph.nodes:
        if not isinstance(node, RekuestActionNodeBase):
            continue
        action = await rekuest.afind(hash=node.hash)
        if action.stateful:
            steps.append(
                step_dependency(
                    step_key(node.id),  # type: ignore[attr-defined]
                    getattr(node, "title", None) or action.name,
                    node.hash,
                )
            )
    return tuple(steps)


async def adeploy_flow(
    flow: Flow, rekuest: Rekuest, runner: IDCoercible
) -> Implementation:
    """Make a flow callable like any action, on the agent of ``runner``.

    ``runner`` is a ``run_flow`` implementation. The action rekuest makes of it takes the
    flow's own arguments and yields its own returns: rekuest binds the flow, packs the
    arguments into ``kwargs`` and unpacks ``returns``. Its stateful steps become dependencies
    of that action (``flow_stateful_steps``): starting the flow binds each to an agent.
    Deploying again redeploys the same interface.
    """
    return await rekuest.acreate_higher_order_implementation(
        lower=runner,
        interface=f"flow:{flow.id}",
        definition=flow_definition(flow),
        config={
            "bound": {"flow": str(flow.id)},
            "args_key": "kwargs",
            "returns_key": "returns",
        },
        dependencies=await flow_stateful_steps(flow, rekuest),
    )
