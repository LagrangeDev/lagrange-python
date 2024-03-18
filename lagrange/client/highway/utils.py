import time
from hashlib import md5, sha1
from typing import Any, Awaitable, BinaryIO, Tuple


def calc_file_hash_and_length(*files: BinaryIO, bs=4096) -> Tuple[bytes, bytes, int]:
    fm, fs, length = md5(), sha1(), 0
    for f in files:
        try:
            while True:
                bl = f.read(bs)
                fm.update(bl)
                fs.update(bl)
                length += len(bl)
                if len(bl) != bs:
                    break
        finally:
            f.seek(0)
    return fm.digest(), fs.digest(), length


def itoa(i: int) -> str:  # int to address(str)
    signed = False
    if i < 0:
        signed = True
    return ".".join([str(p) for p in i.to_bytes(4, "big", signed=signed)])


async def timeit(func: Awaitable) -> Tuple[float, Any]:
    start = time.time()
    result = await func
    return time.time() - start, result
