import asyncio
from typing import List, Optional
from fluss.engine.atoms.helpers import index_for_handle
from fluss.engine.atoms.combination.base import CombinationAtom
from fluss.engine.events import (
    CompleteOutEvent,
    ErrorOutEvent,
    EventType,
    NextInEvent,
    NextOutEvent,
)
import logging
from pydantic import Field

logger = logging.getLogger(__name__)


class WithLatestAtom(CombinationAtom):
    """Emit on the first stream, combined with the latest value of every other stream.

    Only an event on the first stream emits, and only once every other stream has
    emitted at least once; the others just update what is latest. The first stream
    completing completes the atom.
    """

    state: List[Optional[NextInEvent]] = Field(default_factory=lambda: [None, None])

    async def run(self):
        self.state = [None for _ in self.node.ins]
        try:
            while True:
                event = await self.get()

                if event.type == EventType.ERROR:
                    await self.transport.put(
                        ErrorOutEvent(
                            handle="return_0",
                            exception=event.exception,
                            source=self.node.id,
                            caused_by=(event.current_t,),
                        )
                    )
                    break

                streamIndex = index_for_handle(event.handle)

                if event.type == EventType.COMPLETE:
                    if streamIndex == 0:
                        await self.transport.put(
                            CompleteOutEvent(
                                handle="return_0",
                                source=self.node.id,
                                caused_by=(event.current_t,),
                            )
                        )
                        break

                if event.type == EventType.NEXT:
                    self.state[streamIndex] = event

                    if streamIndex == 0 and all(x is not None for x in self.state):
                        value = ()
                        caused_by = ()
                        for inevent in self.state:
                            value += inevent.value
                            caused_by += (inevent.current_t,)

                        await self.transport.put(
                            NextOutEvent(
                                handle="return_0",
                                value=value,
                                source=self.node.id,
                                caused_by=caused_by,
                            )
                        )

        except asyncio.CancelledError as e:
            logger.warning(f"Atom {self.node} is getting cancelled")
            raise e

        except Exception:
            logger.exception(f"Atom {self.node} excepted")
