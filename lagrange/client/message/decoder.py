import zlib
from typing import Tuple, List, Dict, Union

from lagrange.utils.binary.protobuf import proto_encode
from lagrange.utils.operator import unpack_dict

from . import elems
from ..server_push.events.group import GroupMessage


def parse_msg_info(pb: dict) -> Tuple[int, str, int, int, int]:
    info, head, body = pb[1], pb[2], pb[3]
    user_id = info[1]
    uid = info[2]
    seq = head[5]
    time = head[6]
    rand = unpack_dict(pb, "3.1.1.3", head.get(7, -1))

    return user_id, uid, seq, time, rand


def parse_msg(rich: List[Dict[int, dict]]) -> List[Dict[str, Union[int, str]]]:
    msg_chain = []
    ignore_next = False
    for raw in rich:
        if not raw or ignore_next:
            ignore_next = False
            continue
        if 1 in raw:  # msg
            msg = raw[1]
            if 1 in msg and 3 in msg:  # At
                buf3 = msg[3] if isinstance(msg[3], bytes) else msg[3].encode()
                if buf3[6]:  # AtAll
                    msg_chain.append({"type": "atall", "text": msg[1]})
                else:  # At
                    msg_chain.append({
                        "type": "at",
                        "text": msg[1],
                        "uin": int.from_bytes(buf3[7:11], "big"),
                        "uid": msg[12][9]
                    })
            else:  # Text
                msg_chain.append({
                    "type": "text",
                    "text": msg[1]
                })
        elif 2 in raw:  # q emoji
            emo = raw[2]
            msg_chain.append({
                "type": "emoji",
                "id": emo[1]
            })
        elif 6 in raw:  # qq大表情
            pass
        elif 8 in raw:  # gpic
            img = raw[8]
            msg_chain.append({
                "type": "image",
                "text": unpack_dict(img, "34.9", "") or "[图片]",
                "url": "https://gchat.qpic.cn" + img[16],
                "name": unpack_dict(img, "2", "undefined"),
                "is_emoji": bool(unpack_dict(img, "34.1", 0))
            })
        elif 9 in raw:  # unknown
            pass
        elif 12 in raw:
            service = raw[12]
            if service[1]:
                jr = service[1]
                sid = service[2]
                if jr[0]:
                    content = zlib.decompress(jr[1:])
                else:
                    content = jr[1:]
                msg_chain.append({
                    "type": "service",
                    "text": f"[service:{sid}]",
                    "raw": content,
                    "id": sid
                })
        elif 16 in raw:  # extra
            # nickname = unpack_dict(raw, "16.2", "")
            pass
        elif 19 in raw:  # video
            pass
        elif 37 in raw:  # unknown
            pass
        elif 45 in raw:  # msg source info
            src = raw[45]
            msg_text = ""
            for v in src[5] if isinstance(src[5], list) else [src[5]]:
                msg_text += unpack_dict(v, "1.1", "")
            # src[10]: optional[grp_id]
            msg_chain.append({
                "type": "quote",
                "text": f"[quote:{msg_text}]",
                "seq": src[1],
                "uin": src[2],
                "timestamp": src[3],
                "uid": src[8][6]
            })
            ignore_next = True
        elif 51 in raw:  # qq mini app or others
            service = raw[51]
            if service[1]:
                jr = service[1]
                if jr[0]:
                    content = zlib.decompress(jr[1:])
                else:
                    content = jr[1:]
                msg_chain.append({
                    "type": "json",
                    "text": f"[json:{len(content)}]",
                    "raw": content
                })
        else:
            print("unknown msg", raw)
    return msg_chain


def parse_grp_msg(pb: dict):
    user_id, uid, seq, time, rand = parse_msg_info(pb)

    grp_id = unpack_dict(pb, "1.8.1")
    grp_name = unpack_dict(pb, "1.8.7")
    sub_id = unpack_dict(pb, "1.4", 0)  # some client may not report it, old pcqq?
    sender = unpack_dict(pb, "1.8.4")
    parsed_msg = parse_msg(unpack_dict(pb, "3.1.2"))
    if isinstance(sender, dict):  # admin or
        sender_name = unpack_dict(sender, "1.-1.2")
    else:
        sender_name = sender

    if isinstance(grp_name, bytes):  # unexpected end of data
        grp_name = grp_name.decode("utf-8", errors="ignore")

    display_msg = ""
    msg_chain: List[elems.T] = []
    for m in parsed_msg:
        if "text" in m:
            try:
                display_msg += m["text"]
            except TypeError:
                # dec proto err, fallback
                m["text"] = proto_encode(m["text"])  # noqa
                display_msg += m["text"].decode()  # noqa

        obj_name = m.pop("type").capitalize()
        if hasattr(elems, obj_name):
            msg_chain.append(
                getattr(elems, obj_name)(**m)
            )

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
        msg_chain=msg_chain
    )

    return msg
