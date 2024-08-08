import asyncio
from typing import TYPE_CHECKING, Any, Callable, Awaitable, Dict, Set, Type, TypeVar

from lagrange.utils.log import log

if TYPE_CHECKING:
    from .events import BaseEvent
    from .client import Client

T = TypeVar("T", bound="BaseEvent")
EVENT_HANDLER = Callable[["Client", T], Awaitable[Any]]


class Events:
    def __init__(self):
        self._task_group: Set[asyncio.Task] = set()
        self._handle_map: Dict[Type["BaseEvent"], EVENT_HANDLER] = {}

    def subscribe(self, event: Type[T], handler: EVENT_HANDLER[T]):
        if event not in self._handle_map:
            self._handle_map[event] = handler
        else:
            raise AssertionError(
                "Event already subscribed to {}".format(self._handle_map[event])
            )

    def unsubscribe(self, event: Type["BaseEvent"]):
        return self._handle_map.pop(event)

    async def _task_exec(self, client: "Client", event: "BaseEvent", handler: EVENT_HANDLER):
        try:
            await handler(client, event)
        except Exception as e:
            log.root.error(
                "Unhandled exception on task {}".format(event), exc_info=e
            )

    def emit(self, event: "BaseEvent", client: "Client"):
        typ = type(event)
        if typ not in self._handle_map:
            log.root.debug(f"Unhandled event: {event}")
            return

        t = asyncio.create_task(self._task_exec(client, event, self._handle_map[typ]))
        self._task_group.add(t)
        t.add_done_callback(self._task_group.discard)
