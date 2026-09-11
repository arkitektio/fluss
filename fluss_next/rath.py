from types import TracebackType
from typing import Optional
from pydantic import Field
from rath import rath
import contextvars

from rath.links.auth import AuthTokenLink

from rath.links.compose import TypedComposedLink
from rath.links.dictinglink import DictingLink
from rath.links.shrink import ShrinkingLink
from rath.links.split import SplitLink

current_fluss_next_rath: contextvars.ContextVar[Optional["FlussRath"]] = contextvars.ContextVar(
    "current_fluss_next_rath", default=None
)


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
        """Set the current fluss next rath to this instance"""
        await super().__aenter__()
        current_fluss_next_rath.set(self)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Unset the current fluss next rath"""
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_fluss_next_rath.set(None)
