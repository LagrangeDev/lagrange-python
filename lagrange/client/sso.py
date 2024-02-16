import struct
import zlib
from io import BytesIO
from typing import Tuple, Union

from lagrange.utils.crypto.tea import qqtea_decrypt


def parse_lv(buffer: BytesIO):  # u32 len only
    length = struct.unpack('>I', buffer.read(4))[0]
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


def parse_oicq_body(raw: bytes, key: bytes, d2_key: bytes) -> bytes:
    flag, enc_type = struct.unpack("!B12xHx", raw[:16])
    print(flag, enc_type)
    print(raw.hex())
    return raw[16:]


def parse_sso_frame(
        buffer: bytes,
        is_body_encrypted=True
) -> Union[
    Tuple[int, int, Tuple[str, bytes, bytes]],
    Tuple[int, int, str]
]:
    buf = BytesIO(buffer)
    head_len, seq, ret_code = struct.unpack("!Iii", buf.read(12))

    extra = parse_lv(buf).decode()
    if ret_code != 0:
        return seq, ret_code, extra
    command_name = parse_lv(buf).decode()
    session_id = parse_lv(buf)
    compress_type = struct.unpack('>I', buf.read(4))[0]

    data = buf.read()
    if data:
        if compress_type == 0:
            pass
        elif compress_type == 1:
            data = zlib.decompress(data)
        elif compress_type == 8:
            data = data[4:]
        else:
            raise TypeError(f"Unsupported compress type {compress_type}")

    data = parse_oicq_body(data, None, None)

    return seq, ret_code, (command_name, session_id, data)
