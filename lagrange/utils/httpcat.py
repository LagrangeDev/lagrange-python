import asyncio
import gzip
import json
import zlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, overload, Literal
from urllib import parse

from .log import log

_logger = log.fork("utils.httpcat")


@dataclass
class HttpResponse:
    code: int
    status: str
    header: Dict[str, str]
    body: bytes
    cookies: Dict[str, str]

    @property
    def decompressed_body(self) -> bytes:
        if "Content-Encoding" in self.header:
            if self.header["Content-Encoding"] == "gzip":
                return gzip.decompress(self.body)
            elif self.header["Content-Encoding"] == "deflate":
                return zlib.decompress(self.body)
            else:
                raise TypeError(
                    "Unsuppoted compress type:", self.header["Content-Encoding"]
                )
        else:
            return self.body

    def json(self, verify_type=True):
        if (
            "Content-Type" in self.header
            and self.header["Content-Type"].find("application/json") == -1
            and verify_type
        ):
            raise TypeError(self.header.get("Content-Type", "NotSet"))
        return json.loads(self.decompressed_body)

    def text(self, encoding="utf-8", errors="strict") -> str:
        return self.decompressed_body.decode(encoding, errors)


class HttpCat:
    def __init__(
        self,
        host: str,
        port: int,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        ssl=False,
        timeout=5,
    ):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.header: Dict[str, str] = headers or {}
        self.cookie: Dict[str, str] = cookies or {}
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._stop_flag = True
        self._timeout = timeout
        self.header["Connection"] = "keep-alive"

    @classmethod
    def _encode_header(
        cls, method: str, path: str, header: Dict[str, str], *, protocol="HTTP/1.1"
    ) -> bytearray:
        ret = bytearray()
        ret += f"{method.upper()} {path} {protocol}\r\n".encode()
        for k, v in header.items():
            ret += f"{k}: {v}\r\n".encode()
        ret += b"\r\n"
        return ret

    @staticmethod
    async def _read_line(reader: asyncio.StreamReader) -> str:
        return (await reader.readline()).rstrip(b"\r\n").decode()

    @staticmethod
    def _parse_url(url: str) -> Tuple[Tuple[str, int], str, bool]:
        purl = parse.urlparse(url)
        if purl.scheme not in ("http", "https"):
            raise ValueError("unsupported scheme:", purl.scheme)
        if purl.netloc.find(":") != -1:
            host, port = purl.netloc.split(":")
        else:
            host = purl.netloc
            if purl.scheme == "https":
                port = 443
            else:
                port = 80
        return (
            (host, int(port)),
            parse.quote(purl.path) + ("?" + purl.query if purl.query else ""),
            purl.scheme == "https",
        )

    @classmethod
    async def _read_all(cls, header: dict, reader: asyncio.StreamReader) -> bytes:
        if header.get("Transfer-Encoding") == "chunked":
            bs = bytearray()
            while True:
                len_hex = await cls._read_line(reader)
                if len_hex:
                    length = int(len_hex, 16)
                    if length:
                        bs += await reader.readexactly(length)
                    else:
                        break
                else:
                    if header.get("Connection") == "close":  # cloudflare?
                        break
                    raise ConnectionResetError("Connection reset by peer")
            return bytes(bs)
        elif "Content-Length" in header:
            return await reader.readexactly(int(header["Content-Length"]))
        else:
            return await reader.read()

    @classmethod
    async def _parse_response(cls, reader: asyncio.StreamReader) -> HttpResponse:
        stat = await cls._read_line(reader)
        if not stat:
            raise ConnectionResetError
        _, code, status = stat.split(" ", 2)
        header = {}
        cookies = {}
        while True:
            head_block = await cls._read_line(reader)
            if head_block:
                k, v = head_block.split(": ")
                if k.title() == "Set-Cookie":
                    name, value = v[: v.find(";")].split("=", 1)
                    cookies[name] = value
                else:
                    header[k.title()] = v
            else:
                break
        return HttpResponse(
            int(code), status, header, await cls._read_all(header, reader), cookies
        )

    @classmethod
    @overload
    async def _request(
        cls,
        host: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        method: str,
        path: str,
        header: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        cookies: Optional[Dict[str, str]] = None,
        wait_rsp: Literal[True] = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> HttpResponse:
        ...

    @classmethod
    @overload
    async def _request(
        cls,
        host: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        method: str,
        path: str,
        header: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        cookies: Optional[Dict[str, str]] = None,
        wait_rsp: Literal[False] = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        ...

    @classmethod
    async def _request(
        cls,
        host: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        method: str,
        path: str,
        header: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        cookies: Optional[Dict[str, str]] = None,
        wait_rsp: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> Optional[HttpResponse]:
        if not loop:
            loop = asyncio.get_running_loop()
        header = {
            "Host": host,
            "Connection": "close",
            "User-Agent": "HttpCat/1.1",
            "Accept-Encoding": "gzip, deflate",
            "Content-Length": "0" if not body else str(len(body)),
            **(header if header else {}),
        }
        if cookies:
            header["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        writer.write(cls._encode_header(method, path, header))
        if body:
            writer.write(body)
        await writer.drain()

        if wait_rsp:
            try:
                return await cls._parse_response(reader)
            finally:
                if header["Connection"] == "close":
                    loop.call_soon(writer.close)

    @classmethod
    async def request(
        cls,
        method: str,
        url: str,
        header: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        cookies: Optional[Dict[str, str]] = None,
        follow_redirect=True,
        conn_timeout=0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> HttpResponse:
        address, path, ssl = cls._parse_url(url)
        if conn_timeout:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(*address, ssl=ssl), conn_timeout
            )
        else:
            reader, writer = await asyncio.open_connection(*address, ssl=ssl)
        resp = await cls._request(
            address[0], reader, writer, method, path, header, body, cookies, True, loop
        )
        _logger.debug(f"request({method})[{resp.code}]: {url}")
        if resp.code // 100 == 3 and follow_redirect:
            return await cls.request(
                method, resp.header["Location"], header, body, cookies
            )
        else:
            return resp

    async def send_request(
        self, method: str, path: str, body=None, follow_redirect=True, conn_timeout=0
    ) -> HttpResponse:
        if self._stop_flag:
            raise AssertionError("connection stopped")
        if not (self._reader and self._writer):
            if conn_timeout:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port, ssl=self.ssl),
                    conn_timeout,
                )
            else:
                reader, writer = await asyncio.open_connection(
                    self.host, self.port, ssl=self.ssl
                )
            self._reader = reader
            self._writer = writer
            _logger.debug(f"connected to {self.host}:{self.port}")

        resp = await self._request(
            self.host,
            self._reader,
            self._writer,
            method,
            path,
            self.header,
            body,
            self.cookie,
            True,
        )
        _logger.debug(
            f"send_request({method})[{resp.code}]: http{'s' if self.ssl else ''}://{self.host}:{self.port}{path}"
        )
        if resp.cookies:
            self.cookie = resp.cookies
        if resp.code // 100 == 3 and follow_redirect:
            return await self.send_request(method, resp.header["Location"], body)
        else:
            return resp

    async def __aenter__(self):
        self._stop_flag = False
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._stop_flag = True
        if self._reader and self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._reader, self._writer = None, None
