import functools
from typing import Coroutine, Dict, Callable, Any

from lagrange.client.wtlogin.sso import SSOPacket

from .log import logger


class PushDeliver:
    def __init__(self):
        self._handle_map: Dict[str, Callable[[SSOPacket], Coroutine[None, None, Any]]] = {}

    def subscribe(self, cmd: str):
        def _decorator(func: Callable[[SSOPacket], Coroutine[None, None, Any]]):
            @functools.wraps(func)
            async def _wrapper(packet: SSOPacket):
                return await func(packet)

            self._handle_map[cmd] = _wrapper  # noqa

        return _decorator

    async def execute(self, cmd: str, sso: SSOPacket):
        if cmd not in self._handle_map:
            logger.warning("unsupported command: {}".format(cmd))
        else:
            await self._handle_map[cmd](sso)


push_handler = PushDeliver()
