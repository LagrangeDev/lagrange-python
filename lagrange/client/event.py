import asyncio
from typing import TYPE_CHECKING, Callable, Coroutine, Dict, List, Type, TypeVar

from lagrange.utils.log import logger

if TYPE_CHECKING:
    from .client import Client

T = TypeVar("T")
EVENT_HANDLER = Callable[["Client", T], Coroutine[None, None, None]]


class Events:
    def __init__(self):
        self._task_group: List[asyncio.Task] = []
        self._handle_map: Dict[Type[T], EVENT_HANDLER] = {}

    def subscribe(self, event: Type[T], handler: EVENT_HANDLER):
        if event not in self._handle_map:
            self._handle_map[event] = handler
        else:
            raise AssertionError(
                "Event already subscribed to {}".format(self._handle_map[event])
            )

    def unsubscribe(self, event: Type[T]):
        return self._handle_map.pop(event)

    async def _task_exec(self, client: "Client", event: T, handler: EVENT_HANDLER):
        try:
            await handler(client, event)
        except Exception as e:
            logger.root.error(
                "Unhandled exception on task {}".format(event), exc_info=e
            )

    def emit(self, event: T, client: "Client"):
        typ = type(event)
        if typ not in self._handle_map:
            logger.root.debug(f"Unhandled event: {event}")
            return

        t = asyncio.create_task(self._task_exec(client, event, self._handle_map[typ]))
        self._task_group.append(t)
        t.add_done_callback(
            lambda _: self._task_group.remove(typ) if typ in self._task_group else None
        )
