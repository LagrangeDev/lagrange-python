import struct
import zlib
from dataclasses import dataclass, field
from io import BytesIO
from typing import Tuple

from lagrange.utils.binary.reader import Reader
from lagrange.utils.crypto.ecdh import ecdh
from lagrange.utils.crypto.tea import qqtea_decrypt


@dataclass
class SSOPacket:
    seq: int
    ret_code: int
    extra: str
    session_id: bytes
    cmd: str = field(default="")
    data: bytes = field(default=b"")


def parse_lv(buffer: BytesIO):  # u32 len only
    length = struct.unpack(">I", buffer.read(4))[0]
    return buffer.read(length - 4)


def parse_sso_header(raw: bytes, d2_key: bytes) -> Tuple[int, str, bytes]:
    buf = BytesIO(raw)
    # parse sso header
    buf.read(4)
    flag, _ = struct.unpack("!BB", buf.read(2))
    uin = parse_lv(buf).decode()

    if flag == 0:  # no encrypted
        dec = buf.read()
    elif flag == 1:  # enc with d2key
        dec = qqtea_decrypt(buf.read(), d2_key)
    elif flag == 2:  # enc with \x00*16
        dec = qqtea_decrypt(buf.read(), bytes(16))
    else:
        raise TypeError(f"invalid encrypt flag: {flag}")
    return flag, uin, dec


def parse_sso_frame(buffer: bytes, is_oicq_body=False) -> SSOPacket:
    reader = Reader(buffer)
    head_len, seq, ret_code = reader.read_struct("!I2i")
    extra = reader.read_string_with_length("u32")  # extra
    cmd = reader.read_string_with_length("u32")
    session_id = reader.read_bytes_with_length("u32")

    if ret_code != 0:
        return SSOPacket(seq=seq, ret_code=ret_code, session_id=session_id, extra=extra)

    compress_type = reader.read_u32()
    reader.read_bytes_with_length("u32", False)

    data = reader.read_bytes_with_length("u32", False)
    if data:
        if compress_type == 0:
            pass
        elif compress_type == 1:
            data = zlib.decompress(data)
        elif compress_type == 8:
            data = data[4:]
        else:
            raise TypeError(f"Unsupported compress type {compress_type}")

    if is_oicq_body and cmd.find("wtlogin") == 0:
        data = parse_oicq_body(data)

    return SSOPacket(
        seq=seq,
        ret_code=ret_code,
        session_id=session_id,
        extra=extra,
        cmd=cmd,
        data=data,
    )


def parse_oicq_body(buffer: bytes) -> bytes:
    flag, enc_type = struct.unpack("!B12xHx", buffer[:16])

    if flag != 2:
        raise ValueError(f"Invalid OICQ response flag. Expected 2, got {flag}.")

    body = buffer[16:-1]
    if enc_type == 0:
        return qqtea_decrypt(body, ecdh["secp192k1"].share_key)
    else:
        raise ValueError(f"Unknown encrypt type: {enc_type}")
