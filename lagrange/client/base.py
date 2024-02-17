import asyncio
from typing import Optional, Tuple, Union

from lagrange.info import AppInfo, DeviceInfo, SigInfo
from .wtlogin.tlv import CommonTlvBuilder, QrCodeTlvBuilder
from .oicq import build_code2d_packet
from .packet import PacketBuilder
from .network import ClientNetwork
from ..utils.binary.reader import Reader
from ..utils.crypto.ecdh import ecdh
from ..utils.crypto.tea import qqtea_decrypt


class BaseClient:
    """
    A base class for all clients
    login only
    """

    def __init__(
            self,
            uin: int,
            app_info: AppInfo,
            device_info: DeviceInfo,
            sig_info: Optional[SigInfo] = None
    ):
        self._uin = uin
        self._sig = sig_info
        self._app_info = app_info
        self._device_info = device_info
        self._network = ClientNetwork(sig_info)
        self._loop_task: Optional[asyncio.Task] = None

        self._online = False

    def get_seq(self) -> int:
        try:
            return self._sig.sequence
        finally:
            self._sig.sequence += 1

    def connect(self) -> None:
        if not self._loop_task:
            self._loop_task = asyncio.create_task(self._network.loop())
        else:
            raise RuntimeError("connect call twice")

    async def stop(self):
        await self._network.stop()

    async def wait_closed(self) -> None:
        await self._network.wait_closed()

    @property
    def app_info(self) -> AppInfo:
        return self._app_info

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def seq(self) -> int:
        return self._sig.sequence

    @property
    def uin(self) -> int:
        return self._uin

    @property
    def online(self) -> bool:
        return self._online

    async def fetch_qrcode(self) -> Union[int, Tuple[bytes, str]]:
        tlv = QrCodeTlvBuilder()
        body = (
            PacketBuilder()
            .write_u16(0)
            .write_u64(0)
            .write_u8(0)
            .write_tlv(
                tlv.t16(
                    self.app_info.app_id,
                    self.app_info.sub_app_id,
                    bytes.fromhex(self.device_info.guid),
                    self.app_info.pt_version,
                    self.app_info.package_name
                ),
                tlv.t1b(),
                tlv.t1d(self.app_info.misc_bitmap),
                tlv.t33(bytes.fromhex(self.device_info.guid)),
                tlv.t35(self.app_info.pt_os_version),
                tlv.t66(self.app_info.pt_os_version),
                tlv.td1(self.app_info.os, self.device_info.device_name)
            ).write_u8(3)
        ).pack()

        seq = self.get_seq()
        packet = build_code2d_packet(
            self.uin,
            seq,
            0x31,
            self.app_info,
            self.device_info,
            self._sig,
            body
        )

        response = await self._network.send(packet, seq)
        decrypted = Reader(qqtea_decrypt(response.data[16:-1], ecdh["secp192k1"].share_key))
        decrypted.read_bytes(54)
        ret_code = decrypted.read_u8()
        qrsig = decrypted.read_bytes_with_length("u16", False)
        tlvs = decrypted.read_tlv()

        if not ret_code and tlvs[0x17]:
            self._sig.qrsig = qrsig
            return tlvs[0x17], Reader(tlvs[209]).read_bytes_with_length("u16").decode()

        return ret_code
