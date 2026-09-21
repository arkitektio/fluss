"""The generic ``run_flow`` action, ready for an app to register.

The rekuest server's "higher order implementation" feature discovers it via the
``run_flow`` interface and forwards validated flow arguments to it. Registering it
is :meth:`FlussService.register_implementations`, so it belongs to the apps
that were built with the fluss service rather than to whatever imported this
module.
"""

from rekuest.actors.types import RegisterConfig
from rekuest.app import AppRegistry
from rekuest.register import register_func

from fluss.engine.actions import flow_actifier, run_flow

# A single actor serves all flow runs, so they must not queue behind each
# other (the FunctionalActor default is "serial").
RUN_FLOW_CONFIG = RegisterConfig(
    interface="run_flow",
    name="Run Flow",
    bypass_expand=True,
    bypass_shrink=True,
    concurrency="parallel",
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
