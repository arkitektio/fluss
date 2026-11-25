"""The base client for fluss"""

import os
from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any, Self

from arkitekt_spec.declare.client import client
from arkitekt_spec.declare.tested import tested_against
from fakts import Alias, Require, TokenLoader
from koil import unkoil, unkoil_gen
from koil.composition import Composition
from pydantic import Field
from rath.origin import origin_context
from rath.task import TASK_HEADER, TaskLike, current_task, token_of
from rath.turms.funcs import TOperation

from fluss.api.schema import FlussApi
from fluss.rath import FlussRath

TESTED = tested_against("fluss")
"""The fluss server this release wants: the one its release job tested it against."""

_API = os.path.join(os.path.dirname(__file__), "api")


@client(
    schema=os.path.join(_API, "schema.graphql"),
    turms=os.path.join(_API, "project.json"),
)
class Fluss(Composition, FlussApi):
    """Fluss

    Every fluss operation is a method of it (``fluss.aget_flow(id)``), mixed in
    from the generated ``FlussApi``. Each generated method hands its operation
    class and variables to ``execute``/``aexecute`` (queries and mutations) or
    ``subscribe``/``asubscribe`` (subscriptions) below, which run it over
    ``rath``. Nothing is looked up: what a call returns remembers the client it
    was called on. Actions ask for it by annotation (``fluss: Fluss``) and are
    handed their app's client.
    """

    rath: FlussRath = Field(
        ...,
        description="The Rath client used to interact with the Rekuest API.",
    )

    @classmethod
    def from_fakts(
        cls,
        fluss: Annotated[
            Alias,
            Require(
                "live.arkitekt.fluss",
                "Where the flows this app can run are kept",
                version=TESTED,
            ),
        ],
        tokens: TokenLoader,
    ) -> Self:
        """Built by a run: talks to the resolved fluss."""
        from fakts.contrib.rath.auth import FaktsAuthLink
        from rath.links.aiohttp import AIOHttpLink
        from rath.links.graphql_ws import GraphQLWSLink
        from rath.links.split import SplitLink

        from fluss.rath import FlussLinkComposition
        from graphql import OperationType

        return cls(
            rath=FlussRath(
                link=FlussLinkComposition(
                    auth=FaktsAuthLink(token_loader=tokens),
                    split=SplitLink(
                        left=AIOHttpLink(
                            endpoint_url=fluss.to_http_path("graphql"),
                            proxy=fluss.proxy,
                            ssl_context=fluss.ssl_context(),
                        ),
                        right=GraphQLWSLink(
                            ws_endpoint_url=fluss.to_ws_path("graphql"),
                            proxy=fluss.proxy,
                            ssl_context=fluss.ssl_context(),
                        ),
                        split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                    ),
                )
            )
        )

    def _serialize(
        self, operation: type[TOperation], variables: dict[str, Any]
    ) -> dict[str, Any]:
        # fluss sends every argument, set or not (no exclude_unset), as it always has.
        return operation.Arguments(**variables).model_dump(by_alias=True)

    def _headers(self, task: TaskLike | None = None) -> dict[str, Any] | None:
        """The per-call headers: the provenance token of the task this call is for.

        ``task`` when the caller named one, else whichever task is running: the
        run a flow creates is then recorded as created through that task.
        """
        token = token_of(task)
        return {TASK_HEADER: token} if token else None

    def execute(
        self,
        operation: type[TOperation],
        variables: dict[str, Any],
        task: TaskLike | None = None,
    ) -> TOperation:
        """Executes a query or mutation in a blocking way."""
        return unkoil(
            self.aexecute,
            operation,
            variables,
            task=task if task is not None else current_task.get(),
        )

    async def aexecute(
        self,
        operation: type[TOperation],
        variables: dict[str, Any],
        task: TaskLike | None = None,
    ) -> TOperation:
        """Executes a query or mutation in a non-blocking way."""
        x = await self.rath.aquery(
            operation.Meta.document,
            self._serialize(operation, variables),
            headers=self._headers(task if task is not None else current_task.get()),
        )
        return operation.model_validate(
            x.data, context=origin_context(client=self, rath=self.rath)
        )

    def subscribe(
        self, operation: type[TOperation], variables: dict[str, Any]
    ) -> Generator[TOperation, None, None]:
        """Subscribes to an operation in a blocking way."""
        return unkoil_gen(self.asubscribe, operation, variables)

    async def asubscribe(
        self, operation: type[TOperation], variables: dict[str, Any]
    ) -> AsyncGenerator[TOperation, None]:
        """Subscribes to an operation in a non-blocking way."""
        async for event in self.rath.asubscribe(
            operation.Meta.document, self._serialize(operation, variables)
        ):
            yield operation.model_validate(
                event.data, context=origin_context(client=self, rath=self.rath)
            )
