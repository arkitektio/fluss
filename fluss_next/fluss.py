"""The base client for fluss next"""

from koil.composition import Composition
from pydantic import Field

from fluss_next.rath import FlussRath


class Fluss(Composition):
    """Fluss

    The Fluss client is a wrapper around the Rath client, which is a GraphQL client
    that is used to interact with the Rekuest API. The Fluss client provides a
    simplified interface for executing queries and mutations using the Rath clien

    """

    rath: FlussRath = Field(
        ...,
        description="The Rath client used to interact with the Rekuest API.",
    )
