import json
import zlib
from typing import TYPE_CHECKING, cast, Literal, Union
from collections.abc import Sequence

from lagrange.client.events.group import GroupMessage
from lagrange.client.events.friend import FriendMessage
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.message.rich_text import Elems, RichText

from . import elems
from .types import Element
from lagrange.utils.binary.reader import Reader
from lagrange.utils.binary.protobuf import proto_encode
from lagrange.pb.message.rich_text.elems import GroupFileExtra, FileExtra
from lagrange.pb.highway.comm import MsgInfo

if TYPE_CHECKING:
    from lagrange.client.client import Client


def parse_msg_info(pb: MsgPushBody) -> tuple[int, str, int, int, int]:
    user_id = pb.response_head.from_uin
    uid = pb.response_head.from_uid
    seq = pb.content_head.seq
    time = pb.content_head.timestamp
    rand = pb.message.body.attrs.get(3, -1)

    return user_id, uid, seq, time, rand


def parse_friend_info(pkg: MsgPushBody) -> tuple[int, str, int, str]:
    info = pkg.response_head
    from_uin = info.from_uin
    from_uid = info.from_uid
    to_uin = info.to_uin
    to_uid = info.to_uid

    return from_uin, from_uid, to_uin, to_uid


async def parse_msg_new(
    client: "Client", pkg: MsgPushBody, fri_id: Union[str, None] = None, grp_id: Union[int, None] = None
) -> Sequence[Element]:
    if not pkg.message or not pkg.message.body:
        if pkg.content_head.sub_type == 4:
            data = FileExtra.decode(pkg.message.buf2)
            return [
                elems.File.pri_paste_build(
                    file_size=data.file.file_size,
                    file_name=data.file.file_name,
                    file_md5=data.file.file_md5,
                    file_uuid=data.file.file_uuid,
                    file_hash=data.file.file_hash,
                )
            ]
    rich: RichText = pkg.message.body
    if rich.ptt:
        ptt = rich.ptt
        file_key = ptt.group_file_key if ptt.group_file_key else ptt.friend_file_key
        return [
            elems.Audio(
                name=ptt.name,
                size=ptt.size,
                id=ptt.file_id,
                md5=ptt.md5,
                time=ptt.time,
                file_key=ptt.group_file_key if ptt.group_file_key else ptt.friend_file_key,
                qmsg=None,
                url=await client.fetch_audio_url(file_key, uid=fri_id, gid=grp_id),
            )
        ]
    el: list[Elems] = rich.content
    msg_chain: list[Element] = []
    ignore_next = False
    for raw in el:
        if not raw or raw == Elems():
            continue
        elif raw.elem_flags2 or raw.extra_info:
            # unused flags
            continue
        elif ignore_next:
            ignore_next = False
            continue
        if raw.text:  # msg
            msg = raw.text
            if msg.string and not msg.attr6_buf:  # Text
                msg_chain.append(elems.Text(text=msg.string))
            elif msg.attr6_buf:  # At
                buf3 = msg.attr6_buf
                if buf3[6]:  # AtAll
                    msg_chain.append(elems.AtAll(text=msg.string))
                else:  # At
                    msg_chain.append(
                        elems.At(
                            text=msg.string,
                            uin=int.from_bytes(buf3[7:11], "big"),
                            uid=str(msg.pb_reserved.get(9)) if msg.pb_reserved else "",
                        )
                    )
            else:
                raise AssertionError("Invalid message")
        elif raw.general_flags and raw.general_flags.PbReserve:
            gf = raw.general_flags
            if gf.PbReserve.grey:
                content = json.loads(gf.PbReserve.grey.body.content)
                msg_chain.append(elems.GreyTips(text=content["gray_tip"]))
        elif raw.face:  # q emoji
            emo = raw.face
            msg_chain.append(elems.Emoji(id=emo.index))
        elif raw.market_face:
            mf = raw.market_face
            msg_chain.append(
                elems.MarketFace(
                    name=mf.name,
                    face_id=mf.face_id,
                    tab_id=mf.tab_id,
                    width=mf.width,
                    height=mf.height,
                )
            )
            ignore_next = True
        elif raw.custom_face:  # gpic
            img = raw.custom_face
            msg_chain.append(
                elems.Image(
                    name=img.file_path,
                    size=img.size,
                    id=img.fileid,
                    md5=img.md5,
                    display_name=img.args.display_name,
                    width=img.width,
                    height=img.height,
                    url="https://gchat.qpic.cn" + img.original_url,
                    is_emoji=img.args.is_emoji,
                    qmsg=None,
                )
            )
        elif raw.not_online_image:
            img = raw.not_online_image
            msg_chain.append(
                elems.Image(
                    name=img.file_path,
                    size=img.file_len,
                    id=int(img.download_path.split("-")[1]),
                    md5=img.file_md5,
                    display_name=img.args.display_name,
                    width=img.width,
                    height=img.height,
                    url="https://gchat.qpic.cn" + img.origin_path,
                    is_emoji=img.args.is_emoji,
                    qmsg=None,
                )
            )
        elif raw.common_elem:
            common = raw.common_elem
            if common.service_type == 2:
                msg_chain.append(
                    elems.Poke(
                        # text=f"[poke:{common.pb_elem[1]}]",
                        id=common.pb_elem[1],
                        f7=common.pb_elem[7],
                        f8=common.pb_elem[8],
                    )
                )
            if common.bus_type in [10, 20]:  # 10: friend, 20: group
                extra = MsgInfo.decode(proto_encode(raw.common_elem.pb_elem))
                index = extra.body[0].index
                uid = client.uid
                gid = pkg.response_head.rsp_grp.gid if common.bus_type == 20 else None
                url = await client.fetch_image_url(
                    bus_type=cast(Literal[10, 20], common.bus_type),
                    node=index,
                    uid=uid,
                    gid=gid,
                )
                msg_chain.append(
                    elems.Image(
                        name=index.info.name,
                        size=index.info.size,
                        id=0,
                        md5=bytes.fromhex(index.info.hash),
                        display_name=extra.biz_info.pic.summary if extra.biz_info.pic.summary else "[图片]",
                        width=index.info.width,
                        height=index.info.height,
                        url=url,
                        is_emoji=extra.biz_info.pic.biz_type != 0,
                        qmsg=None,
                    )
                )
        elif raw.trans_elem:
            elem_type, trans = raw.trans_elem.elem_type, raw.trans_elem.elem_value
            if elem_type == 24:
                reader = Reader(trans)
                reader.read_bytes(1)
                data = reader.read_bytes_with_length("u16", False)
                file_extra = GroupFileExtra.decode(data)
                msg_chain.append(
                    elems.File.grp_paste_build(
                        file_size=file_extra.inner.info.file_size,
                        file_name=file_extra.inner.info.file_name,
                        file_md5=file_extra.inner.info.file_md5,
                        file_id=file_extra.inner.info.file_id,
                    )
                )
        elif raw.rich_msg:
            service = raw.rich_msg
            if service.template:
                jr = service.template
                sid = service.service_id
                if jr[0]:
                    content = zlib.decompress(jr[1:])
                else:
                    content = jr[1:]
                msg_chain.append(elems.Service(id=sid, raw=content))
            ignore_next = True
        elif raw.open_data:
            msg_chain.append(elems.Raw(data=raw.open_data.data))
        elif raw.src_msg:  # msg source info
            src = raw.src_msg
            msg_text = ""

            for v in src.elems:
                elem = v.get(1, {1: b""})[1]
                if isinstance(elem, dict):
                    msg_text += proto_encode(elem).decode()
                else:
                    msg_text += elem.decode()
            # src[10]: optional[grp_id]
            msg_chain.append(
                elems.Quote(
                    seq=src.seq,
                    uin=src.uin,
                    timestamp=src.timestamp,
                    uid=src.pb_reserved.uid,
                    msg=msg_text,
                )
            )
            ignore_next = True
        elif raw.mini_app:  # qq mini app or others
            service = raw.mini_app.template

            if service[0]:
                content = zlib.decompress(service[1:])
            else:
                content = service[1:]
            msg_chain.append(elems.Json(raw=content))
            ignore_next = True
        # elif 53 in raw:  # q emoji
        #     qe = raw[53]
        #     typ = qe[1]
        #     if typ == 33:  # sm size
        #         eid = qe[2][1]
        #         text = qe[2].get(2, f"[se:{eid}]")
        #     elif typ == 37:  # bg size
        #         eid = qe[2][3]
        #         text = qe[2][7]
        #     elif typ == 48:
        #         voice = unpack_dict(qe, "2.1.1.1")
        #     else:
        #         raise AttributeError("unknown type of reaction: ", qe)
        #
        #     msg_chain.append({
        #         "type": "reaction",
        #         "text": text,
        #         "show_type": typ,
        #         "id": eid
        #     })
        elif raw.video_file:
            video = raw.video_file

            msg_chain.append(
                elems.Video(
                    id=0,
                    time=video.length,
                    name=video.name,
                    size=video.size,
                    file_key=video.id,
                    md5=video.video_md5,
                    width=video.width,
                    height=video.height,
                    qmsg=None,
                    url="",  # TODO: fetch video url
                )
            )
        else:
            pass
            # print("unknown msg", raw)
    return msg_chain


async def parse_friend_msg(client: "Client", pkg: MsgPushBody) -> FriendMessage:
    from_uin, from_uid, to_uin, to_uid = parse_friend_info(pkg)

    seq = pkg.content_head.seq
    msg_id = pkg.content_head.msg_id
    timestamp = pkg.content_head.timestamp
    parsed_msg = await parse_msg_new(client, pkg, fri_id=from_uid, grp_id=None)
    msg_text = "".join([getattr(msg, "display", "") for msg in parsed_msg])

    return FriendMessage(
        from_uin=from_uin,
        from_uid=from_uid,
        to_uin=to_uin,
        to_uid=to_uid,
        seq=seq,
        msg_id=msg_id,
        timestamp=timestamp,
        msg=msg_text,
        msg_chain=list(parsed_msg),
    )


async def parse_grp_msg(client: "Client", pkg: MsgPushBody) -> GroupMessage:
    user_id, uid, seq, time, rand = parse_msg_info(pkg)

    grp_id = pkg.response_head.rsp_grp.gid
    grp_name = pkg.response_head.rsp_grp.grp_name
    sub_id = pkg.response_head.sigmap  # some client may not report it, old pcqq?
    sender_name = pkg.response_head.rsp_grp.sender_name
    sender_type = pkg.response_head.type

    if isinstance(grp_name, bytes):  # unexpected end of data
        grp_name = grp_name.decode("utf-8", errors="ignore")

    parsed_msg = await parse_msg_new(client, pkg, fri_id=None, grp_id=grp_id)
    msg_text = "".join([getattr(msg, "display", "") for msg in parsed_msg])

    return GroupMessage(
        uin=user_id,
        uid=uid,
        nickname=sender_name,
        seq=seq,
        time=time,
        rand=rand,
        grp_id=grp_id,
        grp_name=grp_name,
        sub_id=sub_id,
        sender_type=sender_type,
        msg=msg_text,
        msg_chain=list(parsed_msg),
    )
