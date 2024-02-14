from hashlib import md5

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


class ECDHPrime:
    id = 0x87
    _p256 = ec.SECP256R1()

    svr_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        _p256,
        bytes.fromhex(
            "04"
            "9D1423332735980EDABE7E9EA451B3395B6F35250DB8FC56F25889F628CBAE3E"
            "8E73077914071EEEBC108F4E0170057792BB17AA303AF652313D17C1AC815E79"
        ),
    )

    client_private_key = ec.generate_private_key(_p256)
    client_public_key = client_private_key.public_key().public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )

    share_key = client_private_key.exchange(ec.ECDH(), svr_public_key)  # uncompressed key


class ECDHSecp:
    id = 0x07
    _p192 = ec.SECP192R1()

    svr_public_key = ec.EllipticCurvePublicKey.from_encoded_point(  # FIXME: Invalid EC Key
        _p192,
        bytes.fromhex(
            "04"
            "928D8850673088B343264E0C6BACB8496D697799F37211DEB25BB73906CB089FEA9639B4E0260498B51A992D50813DA8"
        ),
    )

    client_private_key = ec.generate_private_key(_p192)
    client_public_key = client_private_key.public_key().public_bytes(
        Encoding.X962, PublicFormat.CompressedPoint
    )

    share_key = md5(client_private_key.exchange(ec.ECDH(), svr_public_key)[:16]).digest()  # compressed key
