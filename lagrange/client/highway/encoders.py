import os
from typing import TYPE_CHECKING

from lagrange.pb.highway.comm import (
    AudioExtInfo,
    CommonHead,
    ExtBizInfo,
    FileInfo,
    FileType,
    PicExtInfo,
    IndexNode,
)
from lagrange.pb.highway.head import (
    DataHighwayHead,
    HighwayTransReqHead,
    LoginSigHead,
    SegHead,
)
from lagrange.pb.highway.req import (
    C2CUserInfo,
    GroupInfo,
    MultiMediaReqHead,
    NTV2RichMediaReq,
    SceneInfo,
    UploadInfo,
    UploadReq,
    DownloadReq,
)

if TYPE_CHECKING:
    from lagrange.utils.image.decoder import ImageInfo


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
    ext_info: bytes,
) -> HighwayTransReqHead:
    return HighwayTransReqHead(
        msg_head=DataHighwayHead(
            uin=str(uin), command=cmd, seq=seq, app_id=sub_app_id, command_id=cmd_id
        ),
        seg_head=SegHead(
            file_size=file_size,
            data_offset=file_offset,
            data_length=blk_size,
            ticket=ticket,
            md5=blk_md5,
            file_md5=file_md5,
        ),
        req_ext_info=ext_info,
        timestamp=timestamp,
        login_head=LoginSigHead(
            login_sig_type=8,
            login_sig=tgt,
            app_id=app_id,
        ),
    )


def encode_upload_img_req(
    grp_id: int,
    uid: str,
    md5: bytes,
    sha1: bytes,
    size: int,
    info: "ImageInfo",
    is_origin=True,
) -> NTV2RichMediaReq:
    assert not (grp_id and uid)
    fn = f"{md5.hex().upper()}.{info.name or 'jpg'}"
    c2c_info = None
    grp_info = None
    c2c_pb = bytes()
    grp_pb = bytes()
    if grp_id:
        scene_type = 2
        grp_info = GroupInfo(grp_id=grp_id)
        grp_pb = bytes.fromhex(
            "0800180020004a00500062009201009a0100aa010c080012001800200028003a00"
        )
    else:
        scene_type = 1
        c2c_info = C2CUserInfo(uid=uid)
        c2c_pb = bytes.fromhex(
            "0800180020004200500062009201009a0100a2010c080012001800200028003a00"
        )

    return NTV2RichMediaReq(
        req_head=MultiMediaReqHead(
            common=CommonHead(cmd=100),
            scene=SceneInfo(
                req_type=2,
                bus_type=1,
                scene_type=scene_type,
                c2c=c2c_info,
                grp=grp_info,
            ),
        ),
        upload=UploadReq(
            infos=[
                UploadInfo(
                    file_info=FileInfo(
                        size=size,
                        hash=md5.hex(),
                        sha1=sha1.hex(),
                        name=fn,
                        type=FileType(type=1, pic_format=info.pic_type.value),
                        width=info.width,
                        height=info.height,
                        is_origin=is_origin,
                    ),
                    sub_type=0,
                )
            ],
            compat_stype=scene_type,
            client_rand_id=int.from_bytes(os.urandom(4), "big"),
            biz_info=ExtBizInfo(
                pic=PicExtInfo(c2c_reserved=c2c_pb, troop_reserved=grp_pb)
            ),
        ),
    )


def encode_audio_upload_req(
    grp_id: int, uid: str, md5: bytes, sha1: bytes, size: int, time: int
) -> NTV2RichMediaReq:
    assert not (grp_id and uid)
    c2c_info = None
    grp_info = None
    if grp_id:
        scene_type = 2
        grp_info = GroupInfo(grp_id=grp_id)
    else:
        scene_type = 1
        c2c_info = C2CUserInfo(uid=uid)
    return NTV2RichMediaReq(
        req_head=MultiMediaReqHead(
            common=CommonHead(
                req_id=4 if grp_id else 1,
                cmd=100
            ),
            scene=SceneInfo(
                req_type=2,
                bus_type=3,
                scene_type=scene_type,
                c2c=c2c_info,
                grp=grp_info,
            ),
        ),
        upload=UploadReq(
            infos=[
                UploadInfo(
                    file_info=FileInfo(
                        size=size,
                        hash=md5.hex(),
                        sha1=sha1.hex(),
                        name=f"{md5.hex()}.amr",
                        type=FileType(type=3, audio_format=1),
                        width=0,
                        height=0,
                        time=time,
                        is_origin=False,
                    ),
                    sub_type=0,
                )
            ],
            compat_stype=scene_type,
            client_rand_id=int.from_bytes(os.urandom(4), "big"),
            biz_info=ExtBizInfo(
                audio=AudioExtInfo(
                    bytes_reserved=b"\x08\x00\x38\x00",
                    pb_reserved=b"",
                    general_flags=b"\x9a\x01\x07\xaa\x03\x04\x08\x08\x12\x00"
                    if grp_id
                    else b"\x9a\x01\x0b\xaa\x03\x08\x08\x04\x12\x04\x00\x00\x00\x00",
                )
            ),
        ),
    )


def encode_audio_down_req(uuid: str, grp_id: int, uid: str):
    assert not (grp_id and uid)
    c2c_info = None
    grp_info = None
    if grp_id:
        scene_type = 2
        grp_info = GroupInfo(grp_id=grp_id)
    else:
        scene_type = 1
        c2c_info = C2CUserInfo(uid=uid)

    return NTV2RichMediaReq(
        req_head=MultiMediaReqHead(
            common=CommonHead(
                req_id=4 if grp_id else 1,
                cmd=200
            ),
            scene=SceneInfo(
                req_type=1,
                bus_type=3,
                scene_type=scene_type,
                c2c=c2c_info,
                grp=grp_info
            ),
        ),
        download=DownloadReq(
            node=IndexNode(
                file_uuid=uuid
            )
        ),
    )


def encode_grp_img_download_req(grp_id: int, node: IndexNode) -> NTV2RichMediaReq:
    return NTV2RichMediaReq(
        req_head=MultiMediaReqHead(
            common=CommonHead(cmd=200),
            scene=SceneInfo(
                req_type=2,
                bus_type=1,
                scene_type=2,
                grp=GroupInfo(grp_id=grp_id),
            )
        ),
        download=DownloadReq(node=node),
    )


def encode_pri_img_download_req(uid: str, node: IndexNode) -> NTV2RichMediaReq:
    return NTV2RichMediaReq(
        req_head=MultiMediaReqHead(
            common=CommonHead(cmd=200),
            scene=SceneInfo(
                req_type=2,
                bus_type=1,
                scene_type=1,
                c2c=C2CUserInfo(uid=uid),
            )
        ),
        download=DownloadReq(node=node),
    )

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
