# from cai.pb.im.cs.cmd0x388 import ReqBody, TryUpImgReq, TryUpPttReq, GetPttUrlReq
# from cai.pb.highway.ptt_center import (
#     PttShortVideoUploadReq,
#     PttShortVideoFileInfo,
#     ExtensionReq,
#     ReqBody as VideoReqBody
# )
from lagrange.utils.binary.protobuf import proto_encode
from typing import Sequence, TYPE_CHECKING

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
        req_head: dict,
        seg_head: dict,
        ext_info: bytes,
        timestamp: int,
        login_head: dict
) -> bytes:
    return proto_encode({
        1: req_head,
        2: seg_head,
        3: ext_info,
        4: timestamp,
        5: login_head
    })


# def encode_upload_img_req(
#         group_code: int,
#         uin: int,
#         md5: bytes,
#         size: int,
#         info: "ImageInfo"
# ) -> ReqBody:
#     fn = f"{md5.hex().upper()}.{info.name or 'jpg'}"
#     return encode_d388_req(subcmd=1, tryup_img=[
#         TryUpImgReq(
#             group_code=group_code,
#             src_uin=uin,
#             file_name=fn.encode(),
#             file_md5=md5,
#             file_size=size,
#             file_id=0,
#             src_term=5,
#             platform_type=9,
#             bu_type=1,
#             pic_type=info.pic_type,
#             pic_width=info.width,
#             pic_height=info.height,
#             build_ver=b"8.8.50.2324",
#             app_pic_type=1052,
#             original_pic=1,
#             srv_upload=0,
#         )
#     ])
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
