import json
import pickle
import hashlib
from abc import ABC
from dataclasses import dataclass, asdict

from typing_extensions import Self

from lagrange.utils.binary.reader import Reader
from lagrange.utils.binary.builder import Builder
from lagrange.utils.binary.protobuf import proto_encode, proto_decode


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
        return cls(
            **json.loads(buffer)  # noqa
        )

    def dump(self) -> bytes:
        return json.dumps(
            asdict(self)
        ).encode()


@dataclass
class BinarySerializer(BaseSerializer):
    def _encode(self) -> bytes:
        data = pickle.dumps(self)
        data_hash = hashlib.sha256(data).digest()

        return (
            Builder()
            .write_bytes(data_hash, True)
            .write_bytes(data, True)
        ).pack()

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
