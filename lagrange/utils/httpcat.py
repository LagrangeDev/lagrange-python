import gzip
import zlib
import json
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Tuple, Union
from urllib import parse

_logger = logging.getLogger("lagrange.utils.httpcat")


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
                raise TypeError("Unsuppoted compress type:", self.header["Content-Encoding"])
        else:
            return self.body

    def json(self, verify_type=True) -> Union[dict, list]:
        if (
            "Content-Type" in self.header and
            self.header["Content-Type"].find("application/json") == -1 and
            verify_type
        ):
            raise TypeError(self.header.get("Content-Type", "NotSet"))
        return json.loads(self.decompressed_body)

    def text(self, encoding="utf-8", errors="strict") -> str:
        return self.decompressed_body.decode(encoding, errors)


class HttpCat:
    @staticmethod
    def _encode_header(
        method: str,
        path: str,
        header: Dict[str, str],
        *,
        protocol="HTTP/1.1"
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
            purl.scheme == "https"
        )

    @classmethod
    async def _read_all(cls, header: dict, reader: asyncio.StreamReader) -> bytes:
        if header.get("Transfer-Encoding") == "chunked":
            bs = bytearray()
            while True:
                length = int(await cls._read_line(reader) or "0", 16)
                if length:
                    bs += await reader.readexactly(length)
                else:
                    break
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
                k, v = head_block.split(": ")  # type: str
                if k.title() == "Set-Cookie":
                    name, value = v[:v.find(";")].split("=", 1)
                    cookies[name] = value
                else:
                    header[k.title()] = v
            else:
                break
        return HttpResponse(
            int(code),
            status,
            header,
            await cls._read_all(header, reader),
            cookies
        )

    @classmethod
    async def _request(
        cls,
        address: Tuple[str, int],
        method: str,
        path: str,
        header: Dict[str, str] = None,
        body: bytes = None,
        cookies: Dict[str, str] = None,
        ssl: bool = False,
        loop: asyncio.AbstractEventLoop = None
    ) -> HttpResponse:
        if not loop:
            loop = asyncio.get_running_loop()
        header = {
            "Host": address[0],
            "Connection": "close",
            "User-Agent": "HttpCat/1.0",
            "Accept-Encoding": "gzip, deflate",
            "Content-Length": "0" if not body else str(len(body)),
            **(header if header else {})
        }
        if cookies:
            header["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        reader, writer = await asyncio.open_connection(*address, ssl=ssl)
        writer.write(cls._encode_header(
            method,
            path,
            header
        ))
        if body:
            writer.write(body)
        await writer.drain()

        try:
            return await cls._parse_response(reader)
        finally:
            loop.call_soon(writer.close)

    @classmethod
    async def request(
        cls,
        method: str,
        url: str,
        header: Dict[str, str] = None,
        body: bytes = None,
        cookies: Dict[str, str] = None,
        follow_redirect=True,
        loop: asyncio.AbstractEventLoop = None
    ) -> HttpResponse:
        address, path, ssl = cls._parse_url(url)
        resp = await cls._request(
            address,
            method,
            path,
            header,
            body,
            cookies,
            ssl,
            loop
        )
        _logger.debug(f"request: {method} {url} {resp.code}")
        if resp.code // 100 == 3 and follow_redirect:
            return await cls.request(
                method,
                resp.header["Location"],
                header,
                body,
                cookies
            )
        else:
            return resp
