import random
import asyncio
import logging
import secrets
from hashlib import md5
from io import BytesIO
from typing import TYPE_CHECKING, List, Tuple, BinaryIO, Optional

from lagrange.utils.image import decoder
from lagrange.utils.crypto.tea import qqtea_encrypt
from lagrange.utils.httpcat import HttpCat
from lagrange.client.message.elems import Image
from lagrange.utils.binary.protobuf import proto_encode, proto_decode
# from cai.pb.highway.protocol.highway_head_pb2 import highway_head
# from cai.pb.highway.ptt_center import PttShortVideoUploadResp

#from .encoders import encode_upload_img_req, encode_upload_voice_req, encode_video_upload_req
from .frame import write_frame
from .utils import to_id, timeit, calc_file_md5_and_length
#from ..message_service.models import ImageElement, VoiceElement, VideoElement, ForwardNode, ForwardMessage
#from .decoders import decode_upload_ptt_resp, decode_upload_image_resp, decode_video_upload_resp, parse_addr
#from ..multi_msg.forward import prepare_upload
#from ..multi_msg.long_msg import build_multi_apply_up_pkg

if TYPE_CHECKING:
    from lagrange.client.client import Client


class HighWaySession:
    def __init__(self, client: "Client", logger: logging.Logger = None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self._client = client
        self._session_sig: Optional[bytes] = None
        self._session_key: Optional[bytes] = None
        self._session_addr_list: Optional[List[Tuple[str, int]]] = []

    async def _get_bdh_session(self):
        rsp = await self._client.send_uni_packet(
            "HttpConn0x6ff_501",
            proto_encode({
                0x501: {
                    1: 0,
                    2: 0,
                    3: 16,
                    4: 1,
                    5: self._client._sig.tgt.hex(),
                    6: 3,
                    7: [1, 5, 10, 21],
                    9: 2,
                    10: 9,
                    11: 8,
                    15: "1.0.1"
                }
            })
        )

        pb = proto_decode(rsp.data)[0x501]

        if not pb:
            raise ValueError("info not found, try again later")
        self._session_sig = pb[1]
        self._session_key = pb[2]
        # for iplist in info.big_data_channel.bigdata_iplists:
        #     for ip in iplist.ip_list:
        #         self._session_addr_list.append((ip.ip, ip.port))

    def _encrypt_ext(self, ext: bytes) -> bytes:
        if not self._session_key:
            raise KeyError("session key not set, try again later?")
        return qqtea_encrypt(ext, self._session_key)

    async def upload_controller(
        self,
        *files: BinaryIO,
        cmd_id: int,
        ticket: bytes,
        ext=None,
        addrs: List[Tuple[str, int]] = None,
        bs=65535
    ) -> Optional[bytes]:
        if not addrs:
            addrs = self._session_addr_list
        for addr in addrs:
            try:
                sec, data = await timeit(
                    self._bdh_uploader(b"PicUp.DataUp", addr, list(files), cmd_id, ticket, ext, block_size=bs)
                )
                self.logger.info("upload complete, use %fms" % (sec * 1000))
                return data
            except TimeoutError:
                self.logger.error(f"server {addr[0]}:{addr[1]} timeout")
                continue
            finally:
                for f in files:
                    f.seek(0)
        else:
            raise ConnectionError("cannot upload, all server failure")

    async def _bdh_uploader(
        self,
        cmd: bytes,
        addr: Tuple[str, int],
        files: List[BinaryIO],
        cmd_id: int,
        ticket: bytes,
        ext: bytes = None,
        *,
        block_size=65535,
    ) -> Optional[bytes]:
        fmd5, fl = calc_file_md5_and_length(*files)
        # reader, writer = await asyncio.open_connection(*addr)
        bc = 0
        total_transfer = 0
        current_file = files.pop(0)
        async with HttpCat(*addr) as session:
            while True:
                bl = current_file.read(block_size)
                if not bl and not files:
                    return ext
                elif not bl:
                    current_file = files.pop(0)
                    continue

                # head = highway_head.ReqDataHighwayHead(
                #     basehead=_create_highway_header(
                #         cmd, 4096, cmd_id, self._client
                #     ),
                #     seghead=highway_head.SegHead(
                #         filesize=fl,
                #         dataoffset=total_transfer,
                #         datalength=len(bl),
                #         serviceticket=ticket,
                #         md5=md5(bl).digest(),
                #         fileMd5=fmd5,
                #     ),
                #     reqExtendinfo=ext,
                # )
                head = ...

                # writer.write(write_frame(head.SerializeToString(), bl))
                # await writer.drain()
                rsp_http = await session.send_request(
                    "POST",
                    f"/cgi-bin/httpconn?htcmd=0x6FF0087&uin={self._client.uin}",
                    write_frame(head, bl)
                )
                total_transfer += len(bl)

                # resp, data = await read_frame(rsp_http.decompressed_body)
                # if resp.errorCode:
                #     raise ConnectionError(resp.errorCode, "upload error", resp)
                # elif resp and ext:
                #     if resp.rspExtendinfo:
                #         ext = resp.rspExtendinfo
                #     if resp.seghead:
                #         if resp.seghead.serviceticket:
                #             self._session_key = resp.seghead.serviceticket

                bc += 1

    # async def upload_image(self, file: BinaryIO, gid: int) -> Image:
    #     fmd5, fl = calc_file_md5_and_length(file)
    #     info = decoder.decode(file)
    #     ret = decode_upload_image_resp(
    #         (
    #             await self._client.send_unipkg_and_wait(
    #                 "ImgStore.GroupPicUp",
    #                 encode_upload_img_req(gid, self._client.uin, fmd5, fl, info).SerializeToString(),
    #             )
    #         ).data
    #     )
    #     if ret.resultCode != 0:
    #         raise ConnectionError(ret.resultCode)
    #     elif not ret.isExists:
    #         self.logger.debug("file not found, uploading...")
    #
    #         await self.upload_controller(file, cmd_id=2, ticket=ret.uploadKey, addrs=ret.uploadAddr, bs=1048576)
    #
    #     if ret.hasMetaData:
    #         image_type = ret.fileType
    #         w, h = ret.width, ret.height
    #     else:
    #         image_type = info.pic_type
    #         w, h = info.width, info.height
    #
    #     return ImageElement(
    #         id=ret.fileId,
    #         filename=to_id(fmd5) + f".{info.name}",
    #         size=fl,
    #         width=w,
    #         height=h,
    #         md5=fmd5,
    #         filetype=image_type,
    #         url="https://gchat.qpic.cn/gchatpic_new/{uin}/{gid}-{file_id}-{fmd5}/0?term=2".format(
    #             uin=self._client.uin,
    #             gid=gid,
    #             file_id=ret.fileId,
    #             fmd5=fmd5.hex().upper()
    #         )
    #     )
    #
    # async def upload_voice(self, file: BinaryIO, gid: int) -> VoiceElement:
    #     fmd5, fl = calc_file_md5_and_length(file)
    #     ext = encode_upload_voice_req(
    #         gid, self._client.uin, fmd5, fl
    #     ).SerializeToString()
    #     if not (self._session_key and self._session_sig):
    #         await self._get_bdh_session()
    #     ret = decode_upload_ptt_resp(
    #         await self.upload_controller(file, cmd_id=29, ticket=self._session_sig, ext=ext)
    #     )
    #     if ret.resultCode:
    #         raise ConnectionError(ret.resultCode, ret.message)
    #     return VoiceElement(
    #         to_id(fmd5) + ".amr",
    #         file_type=4,
    #         file_id=ret.fileId,
    #         from_uin=self._client.uin,
    #         md5=fmd5,
    #         size=fl,
    #         group_file_key=ret.uploadKey,
    #         url=f"https://grouptalk.c2c.qq.com/?ver=0&rkey={ret.uploadKey.hex()}&filetype=4%voice_codec=0",
    #     )
    #
    # async def upload_video(self, file: BinaryIO, thumb: BinaryIO, gid: int) -> VideoElement:
    #     thumb_md5, thumb_size = calc_file_md5_and_length(thumb)
    #     video_md5, video_size = calc_file_md5_and_length(file)
    #     req = encode_video_upload_req(
    #         random.randint(300000000, 900000000),
    #         self._client.uin, gid,
    #         video_md5, thumb_md5,
    #         video_size, thumb_size
    #     )
    #     ret = decode_video_upload_resp(
    #         (await self._client.send_unipkg_and_wait(
    #             "PttCenterSvr.GroupShortVideoUpReq",
    #             req.SerializeToString()
    #         )).data
    #     ).PttShortVideoUpload_Resp
    #     if ret.retCode:
    #         raise ConnectionError(ret.retCode, ret.retMsg)  # -327: file too big
    #     elif ret.fileExist:
    #         file_id = ret.fileid.encode()
    #     else:
    #         self.logger.debug("file not found, uploading...")
    #
    #         if not (self._session_key and self._session_sig):
    #             self._decode_bdh_session()
    #         ext_data = await self.upload_controller(
    #             thumb,
    #             file,
    #             cmd_id=25,
    #             ticket=self._session_sig,
    #             ext=self._encrypt_ext(req.PttShortVideoUpload_Req.SerializeToString())
    #         )
    #         resp = PttShortVideoUploadResp.FromString(ext_data)
    #         if resp.retCode:
    #             raise ConnectionError(ret.retCode, ret.retMsg)
    #
    #         file_id = resp.fileid.encode()
    #     return VideoElement(
    #         video_md5.hex() + ".mp4",
    #         video_md5,
    #         file_id,
    #         video_size,
    #         120,  # not parse
    #         "server",
    #         thumb_size,
    #         thumb_md5
    #     )
    #
    # async def upload_forward_msg(self, forward: List[ForwardNode], gid: int) -> ForwardMessage:
    #     data, fmd5 = prepare_upload(forward, 0, gid, random.randint(3000000, 80000000))
    #     body, resp = await build_multi_apply_up_pkg(self._client, gid, data, fmd5, 2)
    #     if resp.result:
    #         raise ConnectionError(resp.result)
    #     await self.upload_controller(
    #         BytesIO(body.SerializeToString()),
    #         cmd_id=27,
    #         ticket=resp.msgSig,
    #         addrs=parse_addr(resp.uint32UpIp, resp.uint32UpPort)
    #     )
    #     return ForwardMessage(
    #         gid,
    #         resp.msgResid,
    #         secrets.token_hex(32),
    #         forward
    #     )