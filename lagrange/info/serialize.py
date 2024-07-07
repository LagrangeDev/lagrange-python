import hashlib
import json
import pickle
from abc import ABC
from dataclasses import asdict, dataclass

from typing_extensions import Self

from lagrange.utils.binary.builder import Builder
from lagrange.utils.binary.reader import Reader


class BaseSerializer(ABC):
    @classmethod
    def load(cls, buffer: bytes) -> Self:
        raise NotImplementedError

    def dump(self) -> bytes:
        raise NotImplementedError


@dataclass
class JsonSerializer(BaseSerializer):
    @classmethod
    def load(cls, buffer: bytes) -> Self:
        return cls(**json.loads(buffer))  # noqa

    def dump(self) -> bytes:
        return json.dumps(asdict(self)).encode()


@dataclass
class BinarySerializer(BaseSerializer):
    def _encode(self) -> bytes:
        data = pickle.dumps(self)
        data_hash = hashlib.sha256(data).digest()

        return (Builder().write_bytes(data_hash, with_length=True).write_bytes(data, with_length=True)).pack()

    @classmethod
    def _decode(cls, buffer: bytes, verify=True) -> Self:
        reader = Reader(buffer)
        data_hash = reader.read_bytes_with_length("u16", False)
        data = reader.read_bytes_with_length("u16", False)
        if verify and data_hash != hashlib.sha256(data).digest():
            raise AssertionError("Data hash does not match")

        return pickle.loads(data)

    @classmethod
    def load(cls, buffer: bytes) -> Self:
        return cls._decode(buffer)

    def dump(self) -> bytes:
        return self._encode()
