import asyncio
from typing import Dict, Callable, TypeVar, Type, Coroutine, TYPE_CHECKING, List

from lagrange.utils.log import logger

from .client import Client

T = TypeVar('T')


class Events:
    def __init__(self):
        self._task_group: List[asyncio.Task] = []
        self._handle_map: Dict[Type[T], Callable[[Client, T], Coroutine[None, None, None]]] = {}

    def subscribe(self, event: Type[T], handler: Callable[[Client, T], Coroutine[None, None, None]]):
        if event not in self._handle_map:
            self._handle_map[event] = handler
        else:
            raise AssertionError("Event already subscribed to {}".format(self._handle_map[event]))

    def unsubscribe(self, event: Type[T]):
        return self._handle_map.pop(event)

    def emit(self, event: T, client: Client):
        typ = type(event)
        if typ not in self._handle_map:
            logger.root.debug(f"Unhandled event: {typ.__name__}")
            return

        t = asyncio.create_task(
            self._handle_map[typ](client, event)
        )
        self._task_group.append(t)
        t.add_done_callback(lambda _: self._task_group.remove(typ) if typ in self._task_group else None)
