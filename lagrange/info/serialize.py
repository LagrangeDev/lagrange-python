import json
from dataclasses import dataclass, asdict
from typing import Self


@dataclass
class JsonSerialization(object):
    @classmethod
    def load(cls, string: str) -> Self:
        return cls(
            **json.loads(string)  # noqa
        )

    def dump(self) -> str:
        return json.dumps(
            asdict(self)
        )
