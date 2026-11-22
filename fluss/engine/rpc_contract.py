import contextlib
from collections.abc import AsyncGenerator, Iterator
from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from arkitekt_runtime.postmans.errors import AssignException
from koil.composition.base import KoiledModel
from pydantic import PrivateAttr
from rekuest.api.schema import Action

from fluss.engine.errors import FlowLogicError
from fluss.engine.steps import STEP_METHOD


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
        kwargs: dict[str, Any],
        reference: str | None = None,
        assign_timeout: float | None = None,
        timeout_is_recoverable: bool = False,
    ): ...

    async def aiterate_raw(
        self,
        kwargs: dict[str, Any],
        reference: str | None = None,
        assign_timeout: float | None = None,
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


@contextlib.contextmanager
def _bound(contract: "DirectContract") -> Iterator[None]:
    """Say what a run without the binding lacks, in the flow's terms.

    A flow that is run by handing it to ``run_flow`` declared nothing, so the server finds no
    dependency for the step. Its refusal is turned into what to do about it.
    """
    try:
        yield
    except AssignException as refused:
        if "not found in parent task dependencies" not in str(refused):
            raise
        raise FlowLogicError(
            f"{contract.action.name} is stateful, so it runs on an agent the run names, and this run named none. "
            "Deploy the flow and run the action that makes of it: starting that one binds the step to an agent."
        ) from refused


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

    dependency: str | None = None
    """The dependency of the run this node's action is bound under, for a stateful action.

    A stateful action is not called by its name: the deployed flow declared the node as a
    dependency (``fluss.engine.deploy``), whoever started the flow bound it to one agent, and
    the calls go to that agent through the binding.
    """

    _calls: int = PrivateAttr(default=0)

    def _caller(self) -> Any:  # noqa: ANN401 -- a Task or a RekuestCaller; they share no base
        """Whichever of the two makes a call of the right kind. Their raw signatures match.

        Without a task the call is a root, which only the caller client starts: the app
        running the flow takes in ``rekuest_caller_service`` for that.
        """
        if self.task is not None:
            return self.task
        if not hasattr(self.rekuest, "acall_raw"):
            raise RuntimeError(
                "A flow run outside a task starts its calls as tasks of their own, which takes "
                "the caller client: give the app rekuest_caller_service, or run the flow as a task."
            )
        return self.rekuest

    def _keyed(self) -> dict[str, Any]:
        """The call key of this node's next call, when it is a task's child.

        A flow's nodes call concurrently, so the steps their calls take differ from one run
        to the next; the node and how often it has called do not. A resumed run finds each
        call it already made again by this key. A root call (no task) has no parent to key by.
        """
        if self.task is None:
            return {}
        self._calls += 1
        return {"call_key": f"{self.reference}:{self._calls}"}

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    async def acall_raw(
        self,
        kwargs: dict[str, Any],
        reference: str | None = None,
        assign_timeout: float | None = None,
        timeout_is_recoverable: bool = False,
    ):
        """Call the function or generator in a blocking or non-blocking way.
        This method should be implemented by the subclass.
        """
        # assign_timeout/timeout_is_recoverable are part of the contract protocol,
        # but the rekuest call has no such options; they were never delivered.
        if self.dependency is not None:
            with _bound(self):
                return await self.task.acall_dependency_raw(
                    self.dependency,
                    STEP_METHOD,
                    kwargs,
                    reference=reference,
                    **self._keyed(),
                )
        return await self._caller().acall_raw(
            kwargs=kwargs,
            action=self.action,
            reference=reference,
            **self._keyed(),
        )

    def aiterate_raw(
        self,
        kwargs: dict[str, Any],
        reference: str | None = None,
        assign_timeout: float | None = None,
        timeout_is_recoverable: bool = False,
    ) -> AsyncGenerator[Any, None]:
        """Call the function or generator in a blocking or non-blocking way.
        This method should be implemented by the subclass.
        """
        if self.dependency is not None:
            return self._aiterate_bound(kwargs, reference)
        return self._caller().aiterate_raw(
            kwargs=kwargs,
            action=self.action,
            reference=reference,
            **self._keyed(),
        )

    async def _aiterate_bound(
        self, kwargs: dict[str, Any], reference: str | None
    ) -> AsyncGenerator[Any, None]:
        """A stateful generator's yields, through the binding of the run."""
        with _bound(self):
            async for value in self.task.aiterate_dependency_raw(
                self.dependency,
                STEP_METHOD,
                kwargs,
                reference=reference,
                **self._keyed(),
            ):
                yield value

    async def aenter(self) -> "DirectContract":
        """Enter the context manager for the direct contract.
        This method should be implemented by the subclass.
        """
        return self
