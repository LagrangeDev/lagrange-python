import zlib
from typing import Dict, List, Tuple, Union

from lagrange.client.events.group import GroupMessage
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.message.rich_text import Elems, RichText

from . import elems


def parse_msg_info(pb: MsgPushBody) -> Tuple[int, str, int, int, int]:
    user_id = pb.response_head.from_uin
    uid = pb.response_head.from_uid
    seq = pb.content_head.seq
    time = pb.content_head.timestamp
    rand = pb.message.body.attrs.get(3, -1)

    return user_id, uid, seq, time, rand


def parse_msg(rich: RichText) -> List[Dict[str, Union[int, str]]]:
    if rich.ptt:
        ptt = rich.ptt
        return [
            {
                "type": "audio",
                "text": f"[audio:{ptt.time}]",
                "time": ptt.time,
                "name": ptt.name,
                "id": ptt.file_id,
                "size": ptt.size,
                "file_key": ptt.group_file_key,
                "md5": ptt.md5,
            }
        ]
    elems: List[Elems] = rich.content
    msg_chain = []
    ignore_next = False
    for raw in elems:
        if not raw or raw == Elems():
            continue
        elif ignore_next:
            ignore_next = False
            continue
        if raw.text:  # msg
            msg = raw.text
            if msg.string and not msg.attr6_buf:  # Text
                msg_chain.append({"type": "text", "text": msg.string})
            elif msg.attr6_buf:  # At
                buf3 = msg.attr6_buf
                if buf3[6]:  # AtAll
                    msg_chain.append({"type": "atall", "text": msg.string})
                else:  # At
                    msg_chain.append(
                        {
                            "type": "at",
                            "text": msg.string,
                            "uin": int.from_bytes(buf3[7:11], "big"),
                            "uid": msg.pb_reserved.get(9),
                        }
                    )
            else:
                raise AssertionError("Invalid message")
        elif raw.face:  # q emoji
            emo = raw.face
            msg_chain.append({"type": "emoji", "id": emo.index})
        elif raw.market_face:  # qq大表情
            print(raw.market_face)
            pass
        elif raw.custom_face:  # gpic
            img = raw.custom_face
            msg_chain.append(
                {
                    "type": "image",
                    "text": img.args.display_name,
                    "url": "https://gchat.qpic.cn" + img.original_url,
                    "name": img.file_path,
                    "is_emoji": img.args.is_emoji,
                    "id": img.fileid,
                    "md5": img.md5,
                    "width": img.width,
                    "height": img.height,
                    "size": img.size,
                }
            )
        # elif 9 in raw:  # unknown
        #     pass
        elif raw.rich_msg:
            service = raw.rich_msg
            if service.template:
                jr = service.template
                sid = service.service_id
                if jr[0]:
                    content = zlib.decompress(jr[1:])
                else:
                    content = jr[1:]
                msg_chain.append(
                    {
                        "type": "service",
                        "text": f"[service:{sid}]",
                        "raw": content,
                        "id": sid,
                    }
                )
            ignore_next = True
        # elif 16 in raw:  # extra
        #     # nickname = unpack_dict(raw, "16.2", "")
        #     pass
        # elif 19 in raw:  # video
        #     video = raw[19]
        #     msg_chain.append({
        #         "type": "video",
        #         "text": "[视频]",
        #         "name": unpack_dict(video, "3", "undefined"),
        #         "id": unpack_dict(video, "1"),  # tlv struct? contain md5, filetype
        #         "md5": unpack_dict(video, "2"),
        #         "width": unpack_dict(video, "7"),
        #         "height": unpack_dict(video, "8"),
        #         "size": unpack_dict(video, "6")
        #     })
        # elif 37 in raw:  # unknown
        #     pass
        elif raw.open_data:
            msg_chain.append(
                {
                    "type": "raw",
                    "text": f"[raw:{len(raw.open_data.data)}]",
                    "data": raw.open_data.data,
                }
            )
        elif raw.src_msg:  # msg source info
            src = raw.src_msg
            msg_text = ""

            for v in src.elems:
                msg_text += v.get(1, {1: b""})[1].decode()
            # src[10]: optional[grp_id]
            msg_chain.append(
                {
                    "type": "quote",
                    "text": f"[quote:{msg_text}]",
                    "seq": src.seq,
                    "uin": src.uin,
                    "timestamp": src.timestamp,
                    "uid": src.pb_reserved[6].decode(),
                }
            )
            ignore_next = True
        elif raw.mini_app:  # qq mini app or others
            service = raw.mini_app.template

            if service[0]:
                content = zlib.decompress(service[1:])
            else:
                content = service[1:]
            msg_chain.append(
                {"type": "json", "text": f"[json:{len(content)}]", "raw": content}
            )
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
        else:
            pass
            # print("unknown msg", raw)
    return msg_chain


def parse_friend_msg(pb: dict):
    uin = pb[1][4]


def parse_grp_msg(pkg: MsgPushBody) -> GroupMessage:
    user_id, uid, seq, time, rand = parse_msg_info(pkg)

    grp_id = pkg.response_head.rsp_grp.gid
    grp_name = pkg.response_head.rsp_grp.grp_name
    sub_id = pkg.response_head.sigmap  # some client may not report it, old pcqq?
    sender_name = pkg.response_head.rsp_grp.sender_name

    parsed_msg = parse_msg(pkg.message.body)

    if isinstance(grp_name, bytes):  # unexpected end of data
        grp_name = grp_name.decode("utf-8", errors="ignore")

    display_msg = ""
    msg_chain: List[elems.T] = []
    for m in parsed_msg:
        if "text" in m:
            display_msg += m["text"]

        obj_name = m.pop("type").capitalize()
        if hasattr(elems, obj_name):
            msg_chain.append(getattr(elems, obj_name)(**m))

    msg = GroupMessage(
        uin=user_id,
        uid=uid,
        nickname=sender_name,
        seq=seq,
        time=time,
        rand=rand,
        grp_id=grp_id,
        grp_name=grp_name,
        sub_id=sub_id,
        msg=display_msg,
        msg_chain=msg_chain,
    )

    return msg
