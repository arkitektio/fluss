"""The generic ``run_flow`` action, ready for an app to register.

The rekuest server's "higher order implementation" feature discovers it via the
``run_flow`` interface and forwards validated flow arguments to it. Registering it
is :meth:`FlussService.register_implementations`, so it belongs to the apps
that were built with the fluss service rather than to whatever imported this
module.
"""

from arkitekt_spec.actions import Execution
from arkitekt_spec.declare.actors.types import RegisterConfig
from arkitekt_spec.declare.app import AppRegistry
from arkitekt_spec.declare.register import register_func

from fluss.engine.actions import flow_actifier, run_flow

# A single actor serves all flow runs, so they must not queue behind each
# other (the FunctionalActor default is "serial"). A flow calls other actions, which
# only a workflow may do; as one, a run whose agent dies is resumed, and the calls its
# nodes already made are found again (see DirectContract's call keys).
RUN_FLOW_CONFIG = RegisterConfig(
    interface="run_flow",
    name="Run Flow",
    bypass_expand=True,
    bypass_shrink=True,
    concurrency="parallel",
    execution=Execution.WORKFLOW,
)


def register_run_flow(app_registry: AppRegistry) -> None:
    """Register ``run_flow`` in ``app_registry``, against its own structures."""
    register_func(
        run_flow,
        structure_registry=app_registry.structure_registry,
        implementation_registry=app_registry,
        config=RUN_FLOW_CONFIG,
        actifier=flow_actifier,
    )


# One actor serves every Python flow run. It calls other actions, so it is a workflow too.
RUN_PYTHON_FLOW_CONFIG = RegisterConfig(
    interface="run_python_flow",
    name="Run Python Flow",
    bypass_expand=True,
    bypass_shrink=True,
    concurrency="parallel",
    execution=Execution.WORKFLOW,
)


def register_run_python_flow(app_registry: AppRegistry) -> None:
    """Register ``run_python_flow`` in ``app_registry`` (needs the ``python`` extra)."""
    from fluss.engine.python.actions import python_flow_actifier, run_python_flow

    register_func(
        run_python_flow,
        structure_registry=app_registry.structure_registry,
        implementation_registry=app_registry,
        config=RUN_PYTHON_FLOW_CONFIG,
        actifier=python_flow_actifier,
    )
