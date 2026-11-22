"""A flow's stateful steps: what a deployed flow declares of them, graph or Python.

A stateful action reads or changes the state of the agent that runs it, so rekuest does not
pick that agent. A flow says which of its steps are such when it is deployed: each becomes a
dependency of the deployed action, bound to one agent when the flow is started, and the run
calls the step through that binding.
"""

import re

from arkitekt_spec.actions import (
    ActionDemandInput,
    ActionDependencyInput,
    AgentDependencyInput,
)

#: The slot a stateful step is called through, in the dependency that names it.
STEP_METHOD = "step"


def step_key(node_id: str) -> str:
    """The dependency key of a graph node's stateful step: the node, spelled as a key."""
    return "step_" + re.sub(r"[^A-Za-z0-9_]", "_", node_id)


def step_dependency(key: str, name: str, action_hash: str) -> AgentDependencyInput:
    """The dependency one stateful step is: the action by its hash, under ``key``.

    Named by its hash, the one agent that implements the step binds without being asked for;
    with several, the run is refused until one is chosen.
    """
    return AgentDependencyInput(
        key=key,
        name=name,
        description=f"The agent that runs {name}. The step is stateful, so the run names one.",
        auto_resolvable=True,
        optional=False,
        action_dependencies=(
            ActionDependencyInput(
                key=STEP_METHOD, demand=ActionDemandInput(hash=action_hash)
            ),
        ),
    )
