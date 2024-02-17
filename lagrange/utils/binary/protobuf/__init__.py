from typing import Union, List, Dict
from typing_extensions import TypeAlias, Self

from lagrange.utils.binary.builder import Builder
from lagrange.utils.binary.reader import Reader

Proto: TypeAlias = Dict[int, "ProtoEncodable"]
LengthDelimited: TypeAlias = Union[str, "Proto", bytes]
ProtoEncodable: TypeAlias = Union[int, float, bool, LengthDelimited, List["ProtoEncodable"], Dict[int, "ProtoEncodable"]]


class ProtoBuilder(Builder):
    def write_varint(self, v: int) -> Self:
        if v >= 127:
            length = 0
            buffer = bytearray(10)

            while v > 127:
                buffer[length] = (v & 127) | 128
                v >>= 7
                length += 1

            buffer[length] = v
            self.write_bytes(buffer[:length+1])
        else:
            self.write_u8(v)

        return self

    def write_length_delimited(self, v: LengthDelimited) -> Self:
        if isinstance(v, dict):
            v = proto_encode(v)
        elif isinstance(v, str):
            v = v.encode("utf-8")

        self.write_varint(len(v)).write_bytes(v)
        return Self


class ProtoReader(Reader):
    def read_varint(self) -> int:
        value = 0
        count = 0

        while True:
            byte = self.read_u8()
            value |= (byte & 0b01111111) << (count * 7)
            count += 1

            if (byte & 0b10000000) <= 0:
                break

        return value

    def read_length_delimited(self) -> bytes:
        length = self.read_varint()
        return self.read_bytes(length)


def _encode(builder: ProtoBuilder, tag: int, value: ProtoEncodable):
    if value is None:
        return

    if isinstance(value, int):
        wire_type = 0
    elif isinstance(value, bool):
        wire_type = 0
    elif isinstance(value, float):
        wire_type = 1
    elif isinstance(value, str) or isinstance(value, bytes) or isinstance(value, dict):
        wire_type = 2
    else:
        raise Exception("Unsupported wire type in protobuf")

    head = tag << 3 | wire_type
    builder.write_varint(head)

    if wire_type == 0:
        if isinstance(value, bool):
            value = 1 if value else 0

        if value >= 0:
            builder.write_varint(value)
        else:
            raise NotImplemented
    elif wire_type == 1:
        raise NotImplemented
    elif wire_type == 2:
        if isinstance(value, dict):
            value = proto_encode(value)
        builder.write_length_delimited(value)
    else:
        raise AssertionError


def proto_decode(data: bytes) -> Proto:
    reader = ProtoReader(data)
    proto = {}

    while reader.get_remain > 0:
        leaf = reader.read_varint()
        tag = leaf >> 3
        wire_type = leaf & 0b111

        if wire_type == 0:
            proto[tag] = reader.read_varint()
        elif wire_type == 2:
            value = reader.read_length_delimited()
            try:  # serialize nested
                proto[tag] = proto_decode(value)
            except:
                proto[tag] = value
        else:
            raise AssertionError

    return proto


def proto_encode(proto: Proto) -> bytes:
    builder = ProtoBuilder()

    for tag in proto:
        value = proto[tag]

        if isinstance(value, list):
            for i in value:
                _encode(builder, tag, i)
        else:
            _encode(builder, tag, value)

    return builder.data
