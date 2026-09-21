"""The fluss service of an arkitekt app, and the types it sends by id.

Declared on one registry: the service first, then the structures whose expanders
ask for the client it returns. An app takes all of it in with
``App(services=[fluss_service])``.
"""

import os
from typing import Annotated

from fakts import Alias, Require, TokenLoader
from fakts.contrib.rath.auth import FaktsAuthLink
from graphql import OperationType
from rath.links.aiohttp import AIOHttpLink
from rath.links.graphql_ws import GraphQLWSLink
from rath.links.split import SplitLink

from rekuest.app import AppRegistry
from rekuest.widgets import SearchWidget

from fluss.api.schema import Flow, Run, SearchFlowsQuery, SearchRunsQuery
from fluss.fluss import Fluss
from fluss.rath import FlussLinkComposition, FlussRath


def build_relative_path(*path: str) -> str:
    """Build a path relative to this file, for the files shipped beside it."""
    return os.path.join(os.path.dirname(__file__), *path)


registry = AppRegistry()
"""What fluss brings to an app: its service, and the types it can send by id."""


@registry.service(
    schema=build_relative_path("api", "schema.graphql"),
    turms=build_relative_path("api", "project.json"),
)
def fluss(
    fluss: Annotated[
        Alias,
        Require("live.arkitekt.fluss", "Where the flows this app can run are kept"),
    ],
    tokens: TokenLoader,
) -> Fluss:
    """Fluss: the flows an app can run."""
    return Fluss(
        rath=FlussRath(
            link=FlussLinkComposition(
                auth=FaktsAuthLink(token_loader=tokens),
                split=SplitLink(
                    left=AIOHttpLink(endpoint_url=fluss.to_http_path("graphql")),
                    right=GraphQLWSLink(ws_endpoint_url=fluss.to_ws_path("graphql")),
                    split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                ),
            )
        )
    )


def _search(query: object) -> SearchWidget:
    """The widget that picks one of these out of the deployment."""
    return SearchWidget(query=query.Meta.document, ward="fluss")  # type: ignore[attr-defined]


@registry.structure("@fluss/flow", widget=_search(SearchFlowsQuery))
async def expand_flow(id: str, fluss: Fluss) -> Flow:
    """A flow, by id."""
    return await fluss.aget_flow(id)


@registry.structure("@fluss/run", widget=_search(SearchRunsQuery))
async def expand_run(id: str, fluss: Fluss) -> Run:
    """A run of a flow, by id. Its query is `run`, not `get_run`."""
    return await fluss.arun(id)


def _contribute_run_flow() -> None:
    """Register the generic ``run_flow`` action fluss brings with it.

    ``run_flow`` asks for a ``rekuest: Rekuest`` beside its ``fluss: Fluss``, and a
    parameter is only a client once the service returning it is on the registry,
    so rekuest's service is taken in first -- as an app would take it in. An app
    that already has it sees the same object again, which is a no-op.

    Imported here rather than at module top: the engine pulls in the whole flow
    runtime, and a package that only sends `Flow` ids around should not pay for it
    until its registry is built.
    """
    from rekuest.arkitekt import rekuest_service

    from fluss.engine.rekuest import register_run_flow

    registry.register_service(rekuest_service)
    register_run_flow(registry)


_contribute_run_flow()
