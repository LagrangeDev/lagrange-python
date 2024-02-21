from typing import Tuple, List, Dict, Union

from lagrange.utils.binary.protobuf import proto_decode, proto_encode
from lagrange.utils.operator import unpack_proto_dict

from .log import logger
from .binder import push_handler
from ..wtlogin.sso import SSOPacket

from .models import elems
from .events.message import GroupMessage


def parse_msg_info(pb: dict) -> Tuple[int, str, int, int, int]:
    info, head, body = pb[1], pb[2], pb[3]
    user_id = info[1]
    uid = info[2]
    seq = head[5]
    time = head[6]
    rand = unpack_proto_dict(pb, "3.1.1.3", head[7])

    return user_id, uid, seq, time, rand


def parse_msg(rich: List[Dict[int, dict]]) -> List[Dict[str, Union[int, str]]]:
    msg_chain = []
    for raw in rich:
        if not raw:
            continue
        if 1 in raw:  # msg
            msg = raw[1]
            if 1 in msg and 3 in msg:  # AtElem
                if isinstance(msg[3], bytes) and msg[3][6]:  # AtAll
                    msg_chain.append({"type": "atall", "text": msg[1]})
                else:  # At
                    msg_chain.append({
                        "type": "at",
                        "text": msg[1],
                        "uin": int.from_bytes(msg[3][7:11], "big") if isinstance(msg[3], bytes)
                        else unpack_proto_dict(msg, "12.4"),
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
        elif 8 in raw:  # gpic
            img = raw[8]
            msg_chain.append({
                "type": "image",
                "text": unpack_proto_dict(img, "34.9", "[图片]"),
                "url": "https://gchat.qpic.cn" + img[16],
                "name": unpack_proto_dict(img, "2", "undefined"),
                "is_emoji": bool(unpack_proto_dict(img, "34.1", 0))
            })
        elif 9 in raw:  # unknown
            pass
        elif 16 in raw:  # extra
            nickname = unpack_proto_dict(raw, "16.2", "")
        elif 37 in raw:  # unknown
            pass
        elif 45 in raw:  # msg source info
            pass
        else:
            print("unknown msg", raw)
    return msg_chain


def parse_grp_msg(pb: dict):
    user_id, uid, seq, time, rand = parse_msg_info(pb)

    grp_id = unpack_proto_dict(pb, "1.8.1")
    grp_name = unpack_proto_dict(pb, "1.8.7")
    parsed_msg = parse_msg(pb[3][1][2])

    display_msg = ""
    msg_chain: List[elems.T] = []
    for m in parsed_msg:
        if "text" in m:
            try:
                display_msg += m["text"]
            except TypeError:
                # dec proto err, fallback
                m["text"] = proto_encode(m["text"])  # noqa
                display_msg += m["text"].encode()

        obj_name = m.pop("type").capitalize()
        if hasattr(elems, obj_name):
            msg_chain.append(
                getattr(elems, obj_name)(**m)
            )

    msg = GroupMessage(
        uin=user_id,
        uid=uid,
        seq=seq,
        time=time,
        rand=rand,
        grp_id=grp_id,
        grp_name=grp_name,
        msg=display_msg,
        msg_chain=msg_chain
    )

    return msg


@push_handler.subscribe("trpc.msg.olpush.OlPushService.MsgPush")
async def msg_push_handler(sso: SSOPacket):
    pb = proto_decode(sso.data)
    typ = unpack_proto_dict(pb, "1.2.1")

    logger.debug("msg_push received, type:{}".format(typ))
    if typ == 82:  # grp msg
        return parse_grp_msg(pb[1])
    elif typ == 166:  # frd msg
        pass
    elif typ == 0x2dc:  # grp event
        sub_typ = pb[1][2][2]
        if sub_typ == 17:  # recall
            pass
        elif sub_typ == 12:  # mute
            pass
