import asyncio
import time
from hashlib import md5
from io import BytesIO
from typing import TYPE_CHECKING, BinaryIO, Optional, Union

from lagrange.client.message.elems import Audio, File, Image, Video
from lagrange.pb.highway.comm import IndexNode
from lagrange.pb.highway.ext import NTV2RichMediaHighwayExt
from lagrange.pb.highway.file_ext import (
    ExcitingBusiInfo,
    ExcitingClientInfo,
    ExcitingFileEntry,
    ExcitingFileNameInfo,
    ExcitingHostConfig,
    ExcitingHostInfo,
    ExcitingUrlInfo,
    FileUploadEntry,
    FileUploadExt,
)
from lagrange.pb.highway.httpconn import HttpConn0x6ffReq, HttpConn0x6ffRsp
from lagrange.pb.highway.rsp import DownloadRsp, NTV2RichMediaResp
from lagrange.pb.message.rich_text.elems import VideoFile
from lagrange.pb.service.file import (
    D6Download,
    D6Req,
    D6Rsp,
    D6Upload,
    D9SendFileReq,
    E37DownloadReq,
    E37DownloadRsp,
    E37UploadReq,
    E37UploadRsp,
)
from lagrange.utils.audio import decoder as decoder_audio
from lagrange.utils.binary.protobuf import proto_decode
from lagrange.utils.crypto.tea import qqtea_encrypt
from lagrange.utils.httpcat import HttpCat
from lagrange.utils.image import decoder as decoder_img
from lagrange.utils.log import log

from .constant import _DEFAULT_VIDEO_THUMBNAIL
from .encoders import (
    encode_audio_down_req,
    encode_audio_upload_req,
    encode_grp_img_download_req,
    encode_highway_head,
    encode_pri_img_download_req,
    encode_upload_img_req,
    encode_video_upload_req,
)
from .frame import read_frame, write_frame
from .utils import calc_file_hash_and_length, timeit

if TYPE_CHECKING:
    from lagrange.client.client import Client


class HighWaySession:
    def __init__(self, client: "Client"):
        self.logger = log.fork("highway")
        self._client = client
        self._session_sig: Optional[bytes] = None
        self._session_key: Optional[bytes] = None
        self._session_addr_list: list[tuple[str, int]] = []

    async def _get_bdh_session(self):
        rsp = await self._client.send_uni_packet(
            "HttpConn.0x6ff_501", HttpConn0x6ffReq.build(self._client._sig.tgt).encode()
        )

        pb = HttpConn0x6ffRsp.decode(rsp.data)
        if not pb:
            raise ValueError("info not found, try again later")
        self._session_sig = pb.body.sig_session
        self._session_key = pb.body.sig_key
        for iplist in pb.body.servers:
            if self._client.using_ipv6:
                for v6 in iplist.v6_addr:
                    self._session_addr_list.append((v6.ip, v6.port))
            for v4 in iplist.v4_addr:
                self._session_addr_list.append((v4.ip, v4.port))

    @classmethod
    def _down_url(cls, info: DownloadRsp) -> str:
        rsp = info.info
        return (
            f"http{'s' if rsp.https_port == 443 else ''}://"
            f"{rsp.domain}{f':{rsp.https_port}' if rsp.https_port not in (80, 443) else ''}"
            f"{rsp.url_path}{info.rkey}"
        )

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
        addrs: Optional[list[tuple[str, int]]] = None,
        bs=65535,
    ) -> Optional[bytes]:
        if not addrs:
            addrs = self._session_addr_list
        for addr in addrs:
            try:
                sec, data = await timeit(
                    self._bdh_uploader(
                        "PicUp.DataUp",
                        addr,
                        list(files),
                        cmd_id,
                        ticket,
                        ext,
                        block_size=bs,
                    )
                )
                self.logger.info("upload complete, use %.2fms" % (sec * 1000))
                return data
            except asyncio.TimeoutError:
                self.logger.error(f"server {addr[0]}:{addr[1]} timeout")
                continue
            finally:
                for f in files:
                    f.seek(0)
        else:
            raise ConnectionError("cannot upload, all server failure")

    async def _bdh_uploader(
        self,
        cmd: str,
        addr: tuple[str, int],
        files: list[BinaryIO],
        cmd_id: int,
        ticket: bytes,
        ext: Optional[bytes] = None,
        *,
        block_size=65535,
    ) -> Optional[bytes]:
        fmd5, _, fl = calc_file_hash_and_length(*files)
        ts = int(time.time() * 1000)
        bc = 0
        total_transfer = 0
        current_file = files.pop(0)
        async with HttpCat(
            *addr,
            headers={
                "Accept-Encoding": "identity",
                "User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2)",
            },
        ) as session:
            while True:
                bl = current_file.read(block_size)
                if not bl and not files:
                    return ext
                elif not bl:
                    current_file = files.pop(0)
                    continue

                head = encode_highway_head(
                    uin=self._client.uin,
                    seq=0,
                    cmd=cmd,
                    cmd_id=cmd_id,
                    file_size=fl,
                    file_offset=total_transfer,
                    file_md5=fmd5,
                    blk_size=len(bl),
                    blk_md5=md5(bl).digest(),
                    ticket=ticket,
                    tgt=self._client._sig.tgt,
                    app_id=self._client.app_info.app_id,
                    sub_app_id=self._client.app_info.sub_app_id,
                    timestamp=ts,
                    ext_info=ext or b"",
                ).encode()

                rsp_http = await session.send_request(
                    "POST",
                    f"/cgi-bin/httpconn?htcmd=0x6FF0087&uin={self._client.uin}",
                    write_frame(head, bl),
                )
                total_transfer += len(bl)

                resp, data = read_frame(BytesIO(rsp_http.decompressed_body))
                if resp.err_code:
                    raise ConnectionError(resp.err_code, "upload error", resp)
                elif resp and ext:
                    if resp.ext_info:
                        ext = resp.ext_info
                    if resp.seg_head:
                        if resp.seg_head.ticket:
                            self._session_key = resp.seg_head.ticket

                bc += 1

    async def upload_image(self, file: BinaryIO, gid=0, uid="") -> Image:
        if not self._session_addr_list:
            await self._get_bdh_session()
        fmd5, fsha1, fl = calc_file_hash_and_length(file)
        info = decoder_img.decode(file)
        self.logger.debug(f"image type: {info.pic_type.name}({info.width}*{info.height})")

        ret = NTV2RichMediaResp.decode(
            (
                await self._client.send_oidb_svc(
                    0x11C4 if gid else 0x11C5,
                    100,
                    encode_upload_img_req(gid, uid, fmd5, fsha1, fl, info).encode(),
                    True
                )
            ).data
        )
        if ret.rsp_head.ret_code != 0:
            raise ConnectionError(ret.rsp_head.ret_code, ret.rsp_head.msg)
        if not ret.upload:
            raise ConnectionError(ret.rsp_head.ret_code, ret.rsp_head.msg)
        if ret.upload.ukey:
            self.logger.debug("file not found, uploading...")

            index = ret.upload.msg_info.body[0].index

            ext = NTV2RichMediaHighwayExt.build(
                index.file_uuid,
                ret.upload.ukey,
                ret.upload.v4_addrs,
                ret.upload.msg_info.body,
                1048576,
                fsha1,
            ).encode()
            if not self._session_sig:
                raise ConnectionError("session sig not found, try again later")
            await self.upload_controller(
                file,
                cmd_id=1004 if gid else 1003,
                ticket=self._session_sig,
                ext=ext,
                addrs=self._session_addr_list,
                bs=1048576,
            )
        w, h = info.width, info.height
        if gid:
            fileid = proto_decode(ret.upload.compat_qmsg).into(7, int)
            url = f"https://gchat.qpic.cn/gchatpic_new/{self._client.uin}/{gid}-{fileid}-{fmd5.hex().upper()}/0?term=2"
        else:
            path = proto_decode(ret.upload.compat_qmsg).into(29, dict[int, bytes])[30]
            fileid = 0
            url = "https://multimedia.nt.qq.com.cn/" + path.decode()

        return Image(
            id=fileid,
            display_name="[图片]" if info.pic_type.name != "gif" else "[动画表情]",
            name=f"{fmd5.hex()}.{info.pic_type.name}",
            size=fl,
            width=w,
            height=h,
            md5=fmd5,
            url=url,
            is_emoji=info.pic_type.name == "gif",
            qmsg=None if gid else ret.upload.compat_qmsg,
        )

    async def get_grp_img_url(self, grp_id: int, node: "IndexNode") -> str:
        ret = NTV2RichMediaResp.decode(
            (
                await self._client.send_oidb_svc(
                    0x11C4,
                    200,
                    encode_grp_img_download_req(
                        grp_id, node
                    ).encode(),
                    True
                )
            ).data
        )
        body = ret.download
        assert body, "Internal error, check log for more detail"
        return f"https://{body.info.domain}{body.info.url_path}{body.rkey}"

    async def get_pri_img_url(self, uid: str, node: IndexNode) -> str:
        ret = NTV2RichMediaResp.decode(
            (
                await self._client.send_oidb_svc(
                    0x11C5,
                    200,
                    encode_pri_img_download_req(
                        uid, node
                    ).encode(),
                    True
                )
            ).data
        )
        body = ret.download
        assert body, "Internal error, check log for more detail"
        return f"https://{body.info.domain}{body.info.url_path}{body.rkey}"

    async def upload_voice(self, file: BinaryIO, gid=0, uid="") -> Audio:
        if not self._session_addr_list:
            await self._get_bdh_session()
        fmd5, fsha1, fl = calc_file_hash_and_length(file)
        info = decoder_audio.decode(file)
        self.logger.debug(f"audio info: {info.type.name}-{info.time:.2f}s")

        ret = NTV2RichMediaResp.decode(
            (
                await self._client.send_oidb_svc(
                    0x126E if gid else 0x126D,
                    100,
                    encode_audio_upload_req(
                        gid, uid, fmd5, fsha1, fl, info.seconds
                    ).encode(), True
                )
            ).data
        )

        if ret.rsp_head.ret_code != 0:
            raise ConnectionError(ret.rsp_head.ret_code, ret.rsp_head.msg)
        if not ret.upload:
            raise ConnectionError(ret.rsp_head.ret_code, ret.rsp_head.msg)
        if ret.upload.ukey:
            self.logger.debug("file not found, uploading...")

            index = ret.upload.msg_info.body[0].index

            ext = NTV2RichMediaHighwayExt.build(
                index.file_uuid,
                ret.upload.ukey,
                ret.upload.v4_addrs,
                ret.upload.msg_info.body,
                1048576,
                fsha1,
            ).encode()
            if not self._session_sig:
                raise ConnectionError("session sig not found, try again later")
            await self.upload_controller(
                file,
                cmd_id=1008 if gid else 1007,
                ticket=self._session_sig,
                ext=ext,
                addrs=self._session_addr_list,
                bs=1048576,
            )

        compat = proto_decode(ret.upload.compat_qmsg, 0).into(4, bytes)
        pt = proto_decode(compat, 0)
        if gid:
            file_id = pt.into(8, int)
            file_key = pt.into(18, bytes)
        else:
            file_id = 0
            file_key = pt.into(3, bytes)
        # print(f"https://grouptalk.c2c.qq.com/?ver=0&rkey={compat[18].hex()}&filetype=4%voice_codec=0")

        return Audio(
            time=info.seconds,
            name=f"{fmd5.hex()}.amr",
            id=file_id,
            md5=fmd5,
            size=fl,
            file_key=file_key.decode(),
            qmsg=None if gid else compat,
            url=await self.get_audio_down_url(file_key.decode(), gid, uid),
        )

    async def get_audio_down_url(self, file_key_or_audio: Union[str, Audio], gid: int = 0, uid: str = "") -> str:
        if not self._session_addr_list:
            await self._get_bdh_session()

        audio_file_key = file_key_or_audio.file_key if isinstance(file_key_or_audio, Audio) else file_key_or_audio

        ret = NTV2RichMediaResp.decode(
            (
                await self._client.send_oidb_svc(
                    0x126E if gid else 0x126D,
                    200,
                    encode_audio_down_req(
                        audio_file_key, gid, uid
                    ).encode(), True
                )
            ).data
        )

        if not (ret and ret.download):
            raise ConnectionError("Internal error, check log for more detail")

        return self._down_url(ret.download)

    async def download_audio(self, audio: Audio, gid=0, uid="") -> BytesIO:
        url = await self.get_audio_down_url(audio, gid, uid)

        # SSLV3_ALERT_HANDSHAKE_FAILURE on ssl env
        http = await HttpCat.request("GET", url.replace("https", "http"))
        if http.code != 200:
            raise ConnectionError(http.code, http.status)

        return BytesIO(http.decompressed_body)

    async def upload_video(self, file: BinaryIO, gid=0, uid="", thumb: Optional[BinaryIO] = None) -> Video:
        if not self._session_addr_list:
            await self._get_bdh_session()
        if thumb is None:
            thumb = BytesIO(_DEFAULT_VIDEO_THUMBNAIL)
        fmd5, fsha1, fl = calc_file_hash_and_length(file)
        tmd5, tsha1, tl = calc_file_hash_and_length(thumb)
        self.logger.debug(f"video info: {fl}B, thumb: {tl}B")

        ret = NTV2RichMediaResp.decode(
            (
                await self._client.send_oidb_svc(
                    0x11EA if gid else 0x11E9,
                    100,
                    encode_video_upload_req(gid, uid, fmd5, fsha1, fl, tmd5, tsha1, tl, 0).encode(),
                    True,
                )
            ).data
        )
        if ret.rsp_head.ret_code != 0:
            raise ConnectionError(ret.rsp_head.ret_code, ret.rsp_head.msg)
        if not ret.upload:
            raise ConnectionError(ret.rsp_head.ret_code, ret.rsp_head.msg)

        index = ret.upload.msg_info.body[0].index
        if ret.upload.ukey:
            self.logger.debug("video not found, uploading...")
            ext = NTV2RichMediaHighwayExt.build(
                index.file_uuid,
                ret.upload.ukey,
                ret.upload.v4_addrs,
                ret.upload.msg_info.body,
                1048576,
                fsha1,
            ).encode()
            if not self._session_sig:
                raise ConnectionError("session sig not found, try again later")
            await self.upload_controller(
                file,
                cmd_id=1005 if gid else 1001,
                ticket=self._session_sig,
                ext=ext,
                addrs=self._session_addr_list,
                bs=1048576,
            )

        if ret.upload.sub_file_info:
            sub = ret.upload.sub_file_info[0]
            thumb_index = ret.upload.msg_info.body[1].index
            if sub.ukey:
                self.logger.debug("thumb not found, uploading...")
                ext = NTV2RichMediaHighwayExt.build(
                    thumb_index.file_uuid,
                    sub.ukey,
                    sub.v4_addrs,
                    ret.upload.msg_info.body,
                    1048576,
                    tsha1,
                ).encode()
                await self.upload_controller(
                    thumb,
                    cmd_id=1006 if gid else 1002,
                    ticket=self._session_sig,
                    ext=ext,
                    addrs=self._session_addr_list,
                    bs=1048576,
                )

        compat = VideoFile.decode(ret.upload.compat_qmsg) if ret.upload.compat_qmsg else None
        return Video(
            name=index.info.name,
            size=index.info.size,
            url="",
            id=0,
            md5=bytes.fromhex(index.info.hash),
            qmsg=None,
            width=index.info.width,
            height=index.info.height,
            time=index.info.time,
            file_key=index.file_uuid,
            msg_info=ret.upload.msg_info,
            compat=compat,
        )

    async def get_video_url(self, node: IndexNode, gid: int = 0, uid: str = "") -> str:
        if not self._session_addr_list:
            await self._get_bdh_session()
        if gid:
            ret = NTV2RichMediaResp.decode(
                (
                    await self._client.send_oidb_svc(0x11C4, 200, encode_grp_img_download_req(gid, node).encode(), True)
                ).data
            )
        else:
            ret = NTV2RichMediaResp.decode(
                (
                    await self._client.send_oidb_svc(0x11C5, 200, encode_pri_img_download_req(uid, node).encode(), True)
                ).data
            )
        if not (ret and ret.download):
            raise ConnectionError("Internal error, check log for more detail")
        return self._down_url(ret.download)

    async def upload_private_file(self, file: BinaryIO, uid: str, file_name: str = "") -> File:
        if not self._session_addr_list:
            await self._get_bdh_session()
        if not file_name:
            file_name = getattr(file, "name", "") or ""
            import os
            file_name = os.path.basename(file_name)
        fmd5, fsha1, fl = calc_file_hash_and_length(file)
        file.seek(0)
        md5_10m = md5(file.read(min(fl, 10 * 1024 * 1024))).digest()
        file.seek(0)

        req = E37UploadReq.build(self._client.uid, uid, fl, file_name, md5_10m, fsha1, fmd5)
        rsp = E37UploadRsp.decode(
            (await self._client.send_oidb_svc(0xE37, 1700, req.encode(), False)).data
        )
        upload = rsp.upload
        if upload.ret_code:
            raise ConnectionError(upload.ret_code, upload.ret_msg)

        if not upload.bool_file_exist:
            ext = FileUploadExt(
                unknown200=1,
                entry=FileUploadEntry(
                    busi_buff=ExcitingBusiInfo(sender_uin=self._client.uin),
                    file_entry=ExcitingFileEntry(
                        file_size=fl,
                        md5=fmd5,
                        check_key=fsha1,
                        md5_s2=fmd5,
                        file_id=upload.uuid,
                        upload_key=upload.upload_key,
                    ),
                    client_info=ExcitingClientInfo(),
                    file_name_info=ExcitingFileNameInfo(file_name=file_name),
                    host=ExcitingHostConfig(
                        hosts=[ExcitingHostInfo(url=ExcitingUrlInfo(host=upload.upload_ip), port=upload.upload_port)]
                    ),
                )
            ).encode()
            await self.upload_controller(
                file,
                cmd_id=95,
                ticket=self._session_sig,
                ext=ext,
                addrs=self._session_addr_list,
            )

        return File(
            file_size=fl,
            file_name=file_name,
            file_md5=fmd5,
            file_url=None,
            file_id=None,
            file_uuid=upload.uuid,
            file_hash=upload.file_addon,
        )

    async def upload_group_file(self, file: BinaryIO, grp_id: int, target_directory: str = "/", file_name: str = "") -> File:
        if not self._session_addr_list:
            await self._get_bdh_session()
        if not file_name:
            file_name = getattr(file, "name", "") or ""
            import os
            file_name = os.path.basename(file_name)
        fmd5, fsha1, fl = calc_file_hash_and_length(file)
        file.seek(0)

        req = D6Req(
            file=D6Upload(
                group_uin=grp_id,
                target_directory=target_directory,
                file_name=file_name,
                local_directory=f"/{file_name}",
                file_size=fl,
                file_sha1=fsha1,
                file_md5=fmd5,
            )
        )
        rsp = D6Rsp.decode(
            (await self._client.send_oidb_svc(0x6D6, 0, req.encode(), True)).data
        )
        upload = rsp.upload
        if not upload or upload.ret_code:
            raise ConnectionError(upload.ret_code if upload else -1, upload.ret_msg if upload else "no upload")

        if not upload.bool_file_exist:
            ext = FileUploadExt(
                entry=FileUploadEntry(
                    busi_buff=ExcitingBusiInfo(
                        sender_uin=self._client.uin,
                        receiver_uin=grp_id,
                        group_code=grp_id,
                    ),
                    file_entry=ExcitingFileEntry(
                        file_size=fl,
                        md5=fmd5,
                        check_key=upload.check_key,
                        md5_s2=fmd5,
                        file_id=upload.file_id,
                        upload_key=upload.file_key,
                    ),
                    client_info=ExcitingClientInfo(),
                    file_name_info=ExcitingFileNameInfo(file_name=file_name),
                    host=ExcitingHostConfig(
                        hosts=[ExcitingHostInfo(url=ExcitingUrlInfo(host=upload.upload_ip), port=upload.upload_port)]
                    ),
                )
            ).encode()
            await self.upload_controller(
                file,
                cmd_id=71,
                ticket=self._session_sig,
                ext=ext,
                addrs=self._session_addr_list,
            )

        return File(
            file_size=fl,
            file_name=file_name,
            file_md5=fmd5,
            file_url=None,
            file_id=upload.file_id,
            file_uuid=None,
            file_hash=None,
        )

    async def get_private_file_url(self, file_uuid: str, file_hash: str, uid: str) -> str:
        req = E37DownloadReq.build(uid, file_uuid, file_hash)
        rsp = E37DownloadRsp.decode(
            (await self._client.send_oidb_svc(0xE37, 1200, req.encode(), False)).data
        )
        if not (rsp.body and rsp.body.result):
            raise ConnectionError("Internal error, check log for more detail")
        result = rsp.body.result
        return f"http://{result.server}:{result.port}{result.url}&isthumb=0"

    async def get_group_file_url(self, grp_id: int, file_id: str) -> str:
        req = D6Req(download=D6Download(group_uin=grp_id, file_id=file_id))
        rsp = D6Rsp.decode(
            (await self._client.send_oidb_svc(0x6D6, 2, req.encode(), True)).data
        )
        download = rsp.download
        if not download or download.ret_code:
            raise ConnectionError(download.ret_code if download else -1, download.ret_msg if download else "no download")
        return f"https://{download.download_dns}/ftn_handler/{download.download_url.hex()}/?fname="

    async def send_group_file(self, grp_id: int, file_id: str):
        req = D9SendFileReq.build(grp_id, file_id)
        rsp = await self._client.send_oidb_svc(0x6D9, 4, req.encode(), False)
        if rsp.ret_code:
            raise AssertionError(rsp.ret_code, rsp.err_msg)

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
