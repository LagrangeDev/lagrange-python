import time
from typing import TypeVar

T = TypeVar('T')


def unpack_dict(pd: dict, rule: str, default: T = None) -> T:
    for r in rule.split("."):
        if int(r) in pd or isinstance(pd, list):
            pd = pd[int(r)]
        else:
            if default is not None:
                return default
            else:
                raise KeyError(r)
    return pd


def timestamp() -> int:
    return int(time.time())
