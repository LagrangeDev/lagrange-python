import time
from typing import Any, TypeVar, Union, overload

T = TypeVar("T")


@overload
def unpack_dict(pd: dict, rule: str) -> Any:
    ...


@overload
def unpack_dict(pd: dict, rule: str, default: T) -> Union[Any, T]:
    ...


def unpack_dict(pd: dict, rule: str, default: Union[T, None] = None) -> Union[Any, T]:
    _pd: Any = pd
    for r in rule.split("."):
        if isinstance(_pd, list) or (isinstance(_pd, dict) and int(r) in _pd):
            _pd = _pd[int(r)]
        elif default is not None:
            return default
        else:
            raise KeyError(r)
    return _pd


def timestamp() -> int:
    return int(time.time())
