import struct
from typing import List, Dict, Any
from .models.elems import (
    T,
    At,
    AtAll,
    Image,
    Json,
    Text,
    Emoji,
)


def build_message(msg_chain: List[T], compatible=True) -> dict:
    msg_pb: List[Dict[int, Any]] = []
    for msg in msg_chain:
        if isinstance(msg, Text):
            msg_pb.append({1: {1: msg.text}})
        elif isinstance(msg, AtAll):
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
        else:
            raise NotImplementedError

    return {
        1: {
            2: msg_pb
        }
    }