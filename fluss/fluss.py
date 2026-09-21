"""The base client for fluss"""

from collections.abc import AsyncGenerator, Generator
from typing import Any

from koil import unkoil, unkoil_gen
from koil.composition import Composition
from pydantic import Field
from rath.origin import origin_context
from rath.turms.funcs import TOperation

from fluss.api.schema import FlussApi
from fluss.rath import FlussRath


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

    def _serialize(self, operation: type[TOperation], variables: dict[str, Any]) -> dict[str, Any]:
        # fluss sends every argument, set or not (no exclude_unset), as it always has.
        return operation.Arguments(**variables).model_dump(by_alias=True)

    def execute(self, operation: type[TOperation], variables: dict[str, Any]) -> TOperation:
        """Executes a query or mutation in a blocking way."""
        return unkoil(self.aexecute, operation, variables)

    async def aexecute(self, operation: type[TOperation], variables: dict[str, Any]) -> TOperation:
        """Executes a query or mutation in a non-blocking way."""
        x = await self.rath.aquery(operation.Meta.document, self._serialize(operation, variables))
        return operation.model_validate(x.data, context=origin_context(client=self, rath=self.rath))

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
