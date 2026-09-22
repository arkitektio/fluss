from types import TracebackType
from typing import Any, AsyncGenerator, Dict, Optional, Protocol, runtime_checkable
from koil.composition.base import KoiledModel
from rekuest.api.schema import Action


@runtime_checkable
class RPCContract(Protocol):
    """An RPC contract is a protocol that defines how
    to call a function or generator in a blocking or non-blocking way.
    """

    async def aenter(self) -> "RPCContract":
        """Enter the context manager for the RPC contract.
        This method should be implemented by the subclass.
        """
        ...

    async def __aenter__(self) -> "RPCContract": ...

    async def acall_raw(
        self,
        kwargs: Dict[str, Any],
        reference: str | None = None,
        assign_timeout: Optional[float] = None,
        timeout_is_recoverable: bool = False,
    ): ...

    async def aiterate_raw(
        self,
        kwargs: Dict[str, Any],
        reference: str | None = None,
        assign_timeout: Optional[float] = None,
        timeout_is_recoverable: bool = False,
    ): ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def __enter__(self) -> "RPCContract": ...

    async def aexit(self) -> "RPCContract":
        """Enter the context manager for the RPC contract.
        This method should be implemented by the subclass.
        """
        return self


class DirectContract(KoiledModel):
    """In a direct contract, the function  is called
    without preliminary reserving the node.
    """

    action: Action
    reference: str
    rekuest: Any
    """The rekuest client the action was looked up through."""
    task: Any = None
    """The task this flow runs for, if any.

    Calls go out through it when there is one -- a call made while a task runs is that
    task's child, and the task is what knows the socket and the assignment. With no task
    the flow is running outside any assignment (``arun_flow(assignment=...)``, which the
    tests use) and the client's own root call is the right thing.
    """

    def _caller(self) -> Any:  # noqa: ANN401 -- a Task or a Rekuest; they share no base
        """Whichever of the two makes a call of the right kind. Their raw signatures match."""
        return self.task if self.task is not None else self.rekuest

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    async def acall_raw(
        self,
        kwargs: Dict[str, Any],
        reference: str | None = None,
        assign_timeout: Optional[float] = None,
        timeout_is_recoverable: bool = False,
    ):
        """Call the function or generator in a blocking or non-blocking way.
        This method should be implemented by the subclass.
        """
        # assign_timeout/timeout_is_recoverable are part of the contract protocol,
        # but the rekuest call has no such options; they were never delivered.
        return await self._caller().acall_raw(
            kwargs=kwargs,
            action=self.action,
            reference=reference,
        )

    def aiterate_raw(
        self,
        kwargs: Dict[str, Any],
        reference: str | None = None,
        assign_timeout: Optional[float] = None,
        timeout_is_recoverable: bool = False,
    ) -> AsyncGenerator[Any, None]:
        """Call the function or generator in a blocking or non-blocking way.
        This method should be implemented by the subclass.
        """
        return self._caller().aiterate_raw(
            kwargs=kwargs,
            action=self.action,
            reference=reference,
        )

    async def aenter(self) -> "DirectContract":
        """Enter the context manager for the direct contract.
        This method should be implemented by the subclass.
        """
        return self
