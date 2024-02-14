import json
import struct
import hashlib
from io import BytesIO
from abc import ABC
from dataclasses import dataclass, asdict
from types import NoneType

from typing_extensions import Self, List

from lagrange.utils.binary.builder import Builder


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
            **json.loads(string)  # noqa
        )

    def dump(self) -> bytes:
        return json.dumps(
            asdict(self)
        ).encode()


@dataclass
class BinarySerializer(BaseSerializer):
    type_map = (None, int, float, str, bytes, bytearray)

    @classmethod
    def _type_to_int(cls, typ) -> int:
        if typ not in cls.type_map:
            raise TypeError(f"Unsupported type {typ}")
        for c, v in enumerate(cls.type_map):
            if v == typ:
                return c

    @classmethod
    def _parse_data(cls, typ: int, data: bytes):
        data_type = cls.type_map[typ]
        if data_type == int:
            return int.from_bytes(data, byteorder="big")
        elif data_type == float:
            return struct.unpack("!f", data)
        elif data_type == str:
            return data.decode()
        elif data_type == bytes:
            return data
        elif data_type == bytearray:
            return bytearray(data)
        elif data_type is None:
            return None
        else:
            raise NotImplementedError

    def _encode(self) -> bytes:
        tlvs: List[bytes] = []
        uid = hashlib.sha256()
        for k, v in asdict(self).items():
            if isinstance(v, int):
                iv = v.to_bytes(8, byteorder="big")
            elif isinstance(v, float):
                iv = struct.pack("!f", v)
            elif isinstance(v, str):
                iv = v.encode()
            elif isinstance(v, (bytes, bytearray)):
                iv = bytes(v)
            elif isinstance(v, NoneType):
                iv = None
            else:
                raise NotImplementedError

            tlv = (
                Builder()
                .write_bytes(iv)
            ).pack(self._type_to_int(type(v)))

            uid.update(tlv)
            tlvs.append(tlv)

        return Builder().write_bytes(uid.digest(), with_length=True).write_tlv(*tlvs).pack()

    @classmethod
    def _decode(cls, buffer: bytes, *, strict=True) -> list:
        uid_l = int.from_bytes(buffer[0:2], "big") + 2
        uid = buffer[2:uid_l]
        data = BytesIO(buffer[uid_l:])
        if strict and hashlib.sha256(data.getbuffer()[2:]).digest() != uid:
            raise AssertionError("Invalid UID, digest mismatch")

        pkg_len = struct.unpack(">H", data.read(2))[0]
        result = []
        for _ in range(pkg_len):
            typ, length = struct.unpack(">HH", data.read(4))
            result.append(
                cls._parse_data(typ, data.read(length))
            )
        return result

    @classmethod
    def load(cls, buffer: bytes) -> Self:
        return cls(
            *cls._decode(buffer)  # noqa
        )

    def dump(self) -> bytes:
        return self._encode()
