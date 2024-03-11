# from cai.pb.im.cs.cmd0x388 import ReqBody, TryUpImgReq, TryUpPttReq, GetPttUrlReq
# from cai.pb.highway.ptt_center import (
#     PttShortVideoUploadReq,
#     PttShortVideoFileInfo,
#     ExtensionReq,
#     ReqBody as VideoReqBody
# )
import os
from lagrange.pb.highway.comm import CommonHead, FileInfo, FileType, ExtBizInfo, PicExtInfo
from lagrange.pb.highway.head import HighwayTransReqHead, DataHighwayHead, SegHead, LoginSigHead
from lagrange.utils.binary.protobuf import proto_encode
from typing import Sequence, TYPE_CHECKING
from lagrange.pb.highway.req import (
    MultiMediaReqHead,
    NTV2RichMediaReq,
    SceneInfo,
    C2CUserInfo,
    GroupInfo,
    UploadReq,
    UploadInfo
)

if TYPE_CHECKING:
    from lagrange.utils.image.decoder import ImageInfo


def encode_req_body(
        seq: int,
        uin: int,
        sub_id: int,
        cmd_id: int,
        cmd: str = "PicUp.DataUp",
        ver: int = 1
) -> dict:
    # return ReqBody(
    #     net_type=3,
    #     subcmd=subcmd,
    #     tryup_img_req=tryup_img,
    #     tryup_ptt_req=tryup_ptt,
    #     getptt_url_req=getptt_url_req,
    # )
    return {
        1: ver,
        2: str(uin),
        3: cmd,
        4: seq,
        6: sub_id,
        7: 16,
        8: cmd_id
    }


def encode_seg_head(
        size: int,
        offset: int,
        length: int,
        ticket: bytes,
        file_md5: bytes,
        chunk_md5: bytes
) -> dict:
    return {
        2: size,
        3: offset,
        4: length,
        6: ticket,
        8: chunk_md5,
        9: file_md5
    }


def encode_login_head(
        tgt: bytes,
        app_id: int,
        sig_type: int = 8
) -> dict:
    return {
        1: sig_type,
        2: tgt,
        3: app_id
    }


def encode_highway_head(
        uin: int,
        seq: int,
        cmd: str,
        cmd_id: int,
        file_size: int,
        file_offset: int,
        file_md5: bytes,
        blk_size: int,
        blk_md5: bytes,
        ticket: bytes,
        tgt: bytes,
        app_id: int,
        sub_app_id: int,
        timestamp: int,
        ext_info: bytes
) -> HighwayTransReqHead:
    return HighwayTransReqHead(
        msg_head=DataHighwayHead(
            uin=str(uin),
            command=cmd,
            seq=seq,
            app_id=sub_app_id,
            command_id=cmd_id
        ),
        seg_head=SegHead(
            file_size=file_size,
            data_offset=file_offset,
            data_length=blk_size,
            ticket=ticket,
            md5=blk_md5,
            file_md5=file_md5
        ),
        req_ext_info=ext_info,
        timestamp=timestamp,
        login_head=LoginSigHead(
            login_sig_type=8,
            login_sig=tgt,
            app_id=app_id,
        )
    )


def encode_upload_img_req(
        grp_id: int,
        md5: bytes,
        sha1: bytes,
        size: int,
        info: "ImageInfo",
        is_origin=True
) -> NTV2RichMediaReq:
    fn = f"{md5.hex().upper()}.{info.name or 'jpg'}"
    scene_type = 2
    return NTV2RichMediaReq(
        req_head=MultiMediaReqHead(
            common=CommonHead(
                cmd=100
            ),
            scene=SceneInfo(
                req_type=2,
                bus_type=1,
                scene_type=scene_type,
                grp=GroupInfo(
                    grp_id=grp_id
                )
            )
        ),
        upload=UploadReq(
            infos=[UploadInfo(
                file_info=FileInfo(
                    size=size,
                    hash=md5.hex(),
                    sha1=sha1.hex(),
                    name=fn,
                    type=FileType(
                        type=1,
                        pic_format=info.pic_type.value
                    ),
                    width=info.width,
                    height=info.height,
                    is_origin=is_origin
                ),
                sub_type=0
            )],
            compat_stype=scene_type,
            client_rand_id=int.from_bytes(os.urandom(4), "big"),
            biz_info=ExtBizInfo(
                pic=PicExtInfo(
                    # c2c_reserved=bytes.fromhex(
                    #     "0800180020004200500062009201009a0100a2010c080012001800200028003a00"
                    # )
                    troop_reserved=bytes.fromhex(
                        "0800180020004a00500062009201009a0100aa010c080012001800200028003a00"
                    )
                )
            )
        )
    )
#
#
# def encode_upload_voice_req(
#         group_code: int,
#         uin: int,
#         md5: bytes,
#         size: int,
#         suffix: str = None,
# ) -> ReqBody:
#     return encode_d388_req(subcmd=3, tryup_ptt=[
#         TryUpPttReq(
#             group_code=group_code,
#             src_uin=uin,
#             file_md5=md5,
#             file_name=f"{md5.hex().upper()}.{'amr' if not suffix else suffix}".encode(),
#             file_size=size,
#             voice_length=size,
#             voice_type=1,
#             codec=0,
#             src_term=5,
#             platform_type=9,
#             bu_type=4,
#             inner_ip=0,
#             build_ver=b"8.8.50.2324",
#             new_up_chan=True,
#         )
#     ])
#
#
# def encode_video_upload_req(
#         seq: int,
#         from_uin: int,
#         to_uin: int,
#         video_md5: bytes,
#         thumb_md5: bytes,
#         video_size: int,
#         thumb_size: int,
# ) -> VideoReqBody:
#     return VideoReqBody(
#         cmd=300,
#         seq=seq,
#         PttShortVideoUpload_Req=PttShortVideoUploadReq(
#             fromuin=from_uin,
#             touin=to_uin,
#             chatType=1,
#             clientType=2,
#             groupCode=to_uin,
#             businessType=1,
#             flagSupportLargeSize=1,
#             PttShortVideoFileInfo=PttShortVideoFileInfo(
#                 fileName=video_md5.hex() + ".mp4",
#                 fileMd5=video_md5,
#                 thumbFileMd5=thumb_md5,
#                 fileSize=video_size,
#                 # will be parse info?
#                 fileResLength=1280,
#                 fileResWidth=760,
#                 fileFormat=3,
#                 fileTime=120,
#                 thumbFileSize=thumb_size
#             )
#         ),
#         extensionReq=[ExtensionReq(
#             subBusiType=0,
#             userCnt=1
#         )]
#     )
#
#
# def encode_get_ptt_url_req(
#         group_code: int,
#         uin: int,
#         file_id: int,
#         file_md5: bytes,
#         file_key: bytes
# ) -> ReqBody:
#     return encode_d388_req(
#         subcmd=4,
#         getptt_url_req=[GetPttUrlReq(
#             group_code=group_code,
#             dst_uin=uin,
#             fileid=file_id,
#             file_md5=file_md5,
#             file_key=file_key,
#             req_term=5,
#             req_platform_type=9,
#             inner_ip=0,
#             bu_type=3,
#             build_ver=b"8.8.50.2324",
#             file_id=0,
#             codec=1,
#             req_transfer_type=2,
#             is_auto=1
#         )]
#     )