import hashlib

from lagrange.info import SigInfo
from lagrange.utils.binary.builder import Builder
from lagrange.utils.binary.protobuf import proto_decode, proto_encode
from lagrange.utils.crypto.aes import aes_gcm_decrypt, aes_gcm_encrypt
from lagrange.utils.crypto.ecdh import ecdh
from lagrange.utils.operator import timestamp

_enc_key = bytes.fromhex(
    "e2733bf403149913cbf80c7a95168bd4ca6935ee53cd39764beebe2e007e3aee"
)


def build_key_exchange_request(uin: int, guid: str) -> bytes:
    p1 = proto_encode({1: uin, 2: guid})

    enc1 = aes_gcm_encrypt(p1, ecdh["prime256v1"].share_key)

    p2 = (
        Builder()
        .write_bytes(ecdh["prime256v1"].public_key)
        .write_u32(1)
        .write_bytes(enc1)
        .write_u32(0)
        .write_u32(timestamp())
    ).pack()
    p2_hash = hashlib.sha256(p2).digest()
    enc_p2_hash = aes_gcm_encrypt(p2_hash, _enc_key)

    return proto_encode(
        {
            1: ecdh["prime256v1"].public_key,
            2: 1,
            3: enc1,
            4: timestamp(),
            5: enc_p2_hash,
        }
    )


def parse_key_exchange_response(response: bytes, sig: SigInfo):
    p = proto_decode(response, 0)

    share_key = ecdh["prime256v1"].exchange(p[3])
    dec_pb = proto_decode(aes_gcm_decrypt(p[1], share_key), 0)

    sig.exchange_key = dec_pb[1]
    sig.key_sig = dec_pb[2]
