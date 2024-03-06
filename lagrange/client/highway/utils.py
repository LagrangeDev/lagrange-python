import time
import uuid
from hashlib import md5
from typing import Any, Tuple, BinaryIO, Awaitable


def calc_file_md5_and_length(*files: BinaryIO, bs=4096) -> Tuple[bytes, int]:
    fm, length = md5(), 0
    for f in files:
        try:
            while True:
                bl = f.read(bs)
                fm.update(bl)
                length += len(bl)
                if len(bl) != bs:
                    break
        finally:
            f.seek(0)
    return fm.digest(), length


def itoa(i: int) -> str:  # int to address(str)
    signed = False
    if i < 0:
        signed = True
    return ".".join([str(p) for p in i.to_bytes(4, "little", signed=signed)])


def to_id(b_uuid: bytes) -> str:
    return f"{{{str(uuid.UUID(bytes=b_uuid)).upper()}}}"


async def timeit(func: Awaitable) -> Tuple[float, Any]:
    start = time.time()
    result = await func
    return time.time() - start, result
