import struct
import zlib
from typing import List, Dict, Any
from .elems import (
    T,
    At,
    AtAll,
    Image,
    Service,
    Reaction,
    Json,
    Text,
    Emoji,
    Raw
)


def build_message(msg_chain: List[T], compatible=True) -> dict:
    msg_pb: List[Dict[int, Any]] = []
    for msg in msg_chain:
        if isinstance(msg, AtAll):
            msg_pb.append({
                1: {
                    1: msg.text,
                    6: b"\x00\x01\x00\x00\x00\x05\x01\x00\x00\x00\x00\x00\x00"
                }
            })
        elif isinstance(msg, At):
            msg_pb.append({
                1: {
                    1: msg.text,
                    6: struct.pack("!xb3xbbI2x", 1, len(msg.text), 0, msg.uin)
                }
            })
        elif isinstance(msg, Emoji):
            msg_pb.append({
                2: {
                    1: msg.id
                }
            })
        elif isinstance(msg, Json):
            msg_pb.append({
                51: {
                    1: b"\x01" + zlib.compress(msg.raw)
                }
            })
        elif isinstance(msg, Image):
            msg_pb.append({
                8: {
                    2: msg.name,
                    7: msg.id,
                    8: 0,
                    9: 0,
                    10: 4294967273,
                    12: 1,
                    13: msg.md5,
                    16: msg.url[21:],  # ignore "https://gchat.qpic.cn"
                    20: 1001,
                    22: msg.width,
                    23: msg.height,
                    25: msg.size,
                    26: 1,
                    34: {
                        1: msg.is_emoji,
                        3: 0,
                        4: 0,
                        9: msg.text,
                        10: 0,
                        21: {1: 0, 2: '', 3: 0, 4: 0, 5: 0, 7: ''},
                        31: "undefined"
                    }
                }
            })
        elif isinstance(msg, Service):
            msg_pb.append({
                12: {
                    1: b"\x01" + zlib.compress(msg.raw),
                    2: msg.id
                }
            })
        elif isinstance(msg, Raw):
            msg_pb.append({
                41: {
                    1: msg.data
                }
            })
        elif isinstance(msg, Reaction):
            if msg.show_type == 33:  # sm size
                body = {
                    1: msg.id
                }
            elif msg.show_type == 37:
                body = {
                    1: '1',
                    2: '15',
                    3: msg.id,
                    4: 1,
                    5: 1,
                    6: '',
                    7: msg.text,
                    9: 1
                }
            else:
                raise ValueError(f"Unknown reaction show_type: {msg.show_type}")
            msg_pb.append({
                53: {
                    1: msg.show_type,
                    2: body,
                    3: 1
                }
            })
        elif isinstance(msg, Text):
            msg_pb.append({1: {1: msg.text}})
        else:
            raise NotImplementedError

    return {
        1: {
            2: msg_pb
        }
    }