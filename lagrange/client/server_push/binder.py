from typing import Any, Callable, Coroutine, Dict, TYPE_CHECKING

from lagrange.client.wtlogin.sso import SSOPacket

from .log import logger

if TYPE_CHECKING:
    from lagrange.client.client import Client


class PushDeliver:
    def __init__(self, client: "Client"):
        self._client = client
        self._handle_map: Dict[
            str, Callable[["Client", SSOPacket], Coroutine[None, None, Any]]
        ] = {}

    def subscribe(self, cmd: str, func: Callable[["Client", SSOPacket], Coroutine[None, None, Any]]):
        self._handle_map[cmd] = func

    async def execute(self, cmd: str, sso: SSOPacket):
        if cmd not in self._handle_map:
            logger.warning(f"Unsupported command: {cmd}")
        else:
            return await self._handle_map[cmd](self._client, sso)
