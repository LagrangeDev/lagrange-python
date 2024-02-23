import asyncio
import traceback
from typing import Optional


class Connection:
    def __init__(
        self,
        host: str,
        port: int,
        ssl: bool = False,
        timeout: Optional[float] = None,
    ) -> None:
        self._host = host
        self._port = port
        self._ssl = ssl
        self._stop_flag = False
        self._stop_ev = asyncio.Event()
        self.timeout = timeout

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def ssl(self) -> bool:
        return self._ssl

    @property
    def writer(self) -> asyncio.StreamWriter:
        if not self._writer:
            raise RuntimeError("Connection closed!")
        return self._writer

    @property
    def reader(self) -> asyncio.StreamReader:
        if not self._reader:
            raise RuntimeError("Connection closed!")
        return self._reader

    @property
    def closed(self) -> bool:
        return not (self._reader or self._writer) or self._stop_flag

    async def wait_closed(self) -> None:
        await self._stop_ev.wait()

    async def connect(self) -> None:
        if self._stop_flag:
            raise RuntimeError("Connection already stopped")
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(
                self.host, self.port, ssl=self.ssl
            ), self.timeout
        )

    async def close(self):
        await self.on_disconnect()
        self._writer.close()
        await self.writer.wait_closed()
        self._reader = None
        self._writer = None

    async def stop(self):
        self._stop_flag = True
        await self.close()
        self._stop_ev.set()

    async def _read_loop(self):
        try:
            while not self.closed:
                length = int.from_bytes(await self.reader.readexactly(4), byteorder="big") - 4
                if length:
                    await self.on_message(length)
                else:
                    await self.close()
        except asyncio.CancelledError:
            await self.on_error()
            await self.stop()
        except Exception as e:
            if not await self.on_error():
                raise e

    async def loop(self):
        while not self._stop_flag:
            await self.connect()
            await self.on_connected()
            await self._read_loop()

    async def on_connected(self):
        ...

    async def on_disconnect(self):
        ...

    async def on_message(self, message_length: int):
        ...

    async def on_error(self) -> bool:
        """use sys.exc_info() to catch exceptions"""
        traceback.print_exc()
        return True
