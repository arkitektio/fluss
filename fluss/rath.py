from types import TracebackType
from pydantic import Field
from rath import rath

from rath.links.auth import AuthTokenLink

from rath.links.compose import TypedComposedLink
from rath.links.dictinglink import DictingLink
from rath.links.shrink import ShrinkingLink
from rath.links.split import SplitLink


class FlussLinkComposition(TypedComposedLink):
    """A link composition for Fluss"""

    shrinking: ShrinkingLink = Field(default_factory=ShrinkingLink)
    dicting: DictingLink = Field(default_factory=DictingLink)
    auth: AuthTokenLink
    split: SplitLink


class FlussRath(rath.Rath):
    """Fluss Rath

    Args:
        rath (_type_): _description_
    """

    async def __aenter__(self) -> "FlussRath":
        """Enter the client.

        Entering does not make it "the current client": only the fluss service
        that owns it becomes current, while it is entered.
        A rath used on its own is passed where it is needed, as ``rath=``.
        """
        await super().__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the client"""
        await super().__aexit__(exc_type, exc_val, exc_tb)
