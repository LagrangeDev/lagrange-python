import gzip
import json
import random
import struct
from uuid import uuid4
import zlib
from typing import TYPE_CHECKING, Any, Callable, Optional
from collections.abc import Coroutine

from lagrange.pb.message.heads import ContentHead, Forward, Grp, ResponseHead
from lagrange.pb.message.longmsg import (
    LongMsgResp,
    PbMultiMsgItem,
    PbMultiMsgNew,
    PbMultiMsgTransmit,
    LongMsgRsp,
)
from lagrange.pb.message.msg import Message
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.message.rich_text import Elems, RichText
from lagrange.pb.message.rich_text.elems import (
    CustomFace,
    ImageReserveArgs,
    Face,
    MiniApp,
    OpenData,
    Ptt,
    RichMsg,
    SrcMsg,
    CommonElem,
    MarketFace as PBMarketFace,
    NotOnlineImage,
    SrcMsgArgs,
    PBGreyTips,
    GeneralFlags,
)
from lagrange.pb.message.rich_text.elems import Text as PBText
from lagrange.pb.highway.comm import PicExtInfo
from lagrange.utils.binary.protobuf import proto_decode

from .elems import (
    At,
    AtAll,
    Audio,
    Emoji,
    Image,
    Json,
    MulitMsg,
    Quote,
    Raw,
    Reaction,
    Service,
    Text,
    Poke,
    MarketFace,
    GreyTips,
    Video,
)
from .types import Element

if TYPE_CHECKING:
    from ..client import Client as Client


async def build_message(
    msg_chain: list[Element], compatible=True, forward_func: Optional[Callable[..., Coroutine[Any, Any, str]]] = None
) -> RichText:
    if not msg_chain:
        raise ValueError("Message chain is empty")
    msg_pb: list[Elems] = []
    msg_ptt: Optional[Ptt] = None
    if not isinstance(msg_chain[0], Audio):
        for msg in msg_chain:
            if isinstance(msg, AtAll):
                msg_pb.append(
                    Elems(
                        text=PBText(
                            string=msg.text,
                            attr6_buf=b"\x00\x01\x00\x00\x00\x05\x01\x00\x00\x00\x00\x00\x00",
                        )
                    )
                )
            elif isinstance(msg, At):
                msg_pb.append(
                    Elems(
                        text=PBText(
                            string=msg.text,
                            attr6_buf=struct.pack("!xb3xbbI2x", 1, len(msg.text), 0, msg.uin),
                            pb_reserved={3: 2, 4: 0, 5: 0, 9: msg.uid, 11: 0},
                        )
                    )
                )
            elif isinstance(msg, Quote):
                msg_pb.append(
                    Elems(
                        src_msg=SrcMsg(
                            seq=msg.seq,
                            uin=msg.uin,
                            timestamp=msg.timestamp,
                            elems=[{1: {1: msg.msg}}],
                            pb_reserved=SrcMsgArgs(uid=msg.uid) if msg.uid else None,
                        )
                    )
                )
                if compatible:
                    text = f"@{msg.uin}"
                    msg_pb.append(
                        Elems(
                            text=PBText(
                                string=text,
                                attr6_buf=struct.pack("!xb3xbbI2x", 1, len(text), 0, msg.uin),
                                pb_reserved={3: 2, 4: 0, 5: 0, 9: msg.uid, 11: 0},
                            )
                        )
                    )
            elif isinstance(msg, Emoji):
                msg_pb.append(Elems(face=Face(index=msg.id)))
            elif isinstance(msg, Json):
                msg_pb.append(Elems(mini_app=MiniApp(template=b"\x01" + zlib.compress(msg.raw))))
            elif isinstance(msg, Image):
                if msg.msg_info and msg.bus_type in (10, 20):
                    # QQ upload response omits PicExtInfo.biz_type; stamp it explicitly
                    # so receivers never see an absent field (None != 0 misjudged as emoji).
                    if msg.msg_info.biz_info.pic is None:
                        msg.msg_info.biz_info.pic = PicExtInfo()
                    msg.msg_info.biz_info.pic.biz_type = 1 if msg.is_emoji else 0
                    msg_pb.append(
                        Elems(
                            common_elem=CommonElem(
                                service_type=48,
                                pb_elem=proto_decode(msg.msg_info.encode(), 0).proto,
                                bus_type=msg.bus_type,
                            )
                        )
                    )
                elif msg.id:  # customface
                    msg_pb.append(
                        Elems(
                            custom_face=CustomFace(
                                file_path=msg.name,
                                fileid=msg.id,
                                file_type=4294967273,
                                md5=msg.md5,
                                original_url=msg.url[21:],
                                image_type=1001,
                                width=msg.width,
                                height=msg.height,
                                size=msg.size,
                                args=ImageReserveArgs(
                                    is_emoji=msg.is_emoji,
                                    display_name=msg.display_name or ("[动画表情]" if msg.is_emoji else "[图片]"),
                                ),
                            )
                        )
                    )
                else:
                    msg_pb.append(Elems(not_online_image=NotOnlineImage.decode(msg.qmsg)))
            elif isinstance(msg, Video):
                if not msg.msg_info:
                    raise ValueError("Video msg_info not set, upload first")
                to_scene = msg.msg_info.biz_info.video.to_scene if msg.msg_info.biz_info.video else None
                msg_pb.append(
                    Elems(
                        common_elem=CommonElem(
                            service_type=48,
                            pb_elem=proto_decode(msg.msg_info.encode(), 0).proto,
                            bus_type=21 if to_scene == 2 else 11,
                        )
                    )
                )
                if msg.compat:
                    msg_pb.append(Elems(video_file=msg.compat))
            elif isinstance(msg, Service):
                msg_pb.append(Elems(rich_msg=RichMsg(template=b"\x01" + zlib.compress(msg.raw), service_id=msg.id)))
            elif isinstance(msg, Raw):
                msg_pb.append(Elems(open_data=OpenData(data=msg.data)))
            elif isinstance(msg, Reaction):
                pass
                # if msg.show_type == 33:  # sm size
                #     body = {
                #         1: msg.id
                #     }
                # elif msg.show_type == 37:
                #     body = {
                #         1: '1',
                #         2: '15',
                #         3: msg.id,
                #         4: 1,
                #         5: 1,
                #         6: '',
                #         7: msg.text,
                #         9: 1
                #     }
                # else:
                #     raise ValueError(f"Unknown reaction show_type: {msg.show_type}")
                # msg_pb.append({
                #     53: {
                #         1: msg.show_type,
                #         2: body,
                #         3: 1
                #     }
                # })
            elif isinstance(msg, MarketFace):
                msg_pb.append(
                    Elems(
                        market_face=PBMarketFace(
                            name=msg.name,
                            item_type=6,
                            face_info=1,
                            face_id=msg.face_id,
                            tab_id=msg.tab_id,
                            sub_type=3,
                            key="0000000000000000",
                            width=msg.width,
                            height=msg.height,
                            pb_reserved={1: {1: msg.width, 2: msg.height}, 8: 1},
                        )
                    )
                )
            elif isinstance(msg, GreyTips):
                content = json.dumps(
                    {
                        "gray_tip": msg.text,
                        "object_type": 3,
                        "sub_type": 2,
                        "type": 4,
                    }
                )
                msg_pb.append(Elems(general_flags=GeneralFlags(PbReserve=PBGreyTips.build(content))))
            elif isinstance(msg, Text):
                msg_pb.append(Elems(text=PBText(string=msg.text)))
            elif isinstance(msg, Poke):
                msg_pb.append(
                    Elems(
                        common_elem=CommonElem(
                            service_type=2,
                            pb_elem={1: msg.id, 7: msg.f7, 8: msg.f8},
                            bus_type=1,
                        )
                    )
                )
            elif isinstance(msg, MulitMsg):
                if msg.resid is None:
                    if forward_func is None:
                        continue
                    msg.resid = await forward_func(msg)
                fileid = str(uuid4())
                template = {
                    "app": "com.tencent.multimsg",
                    "config": {"autosize": 1, "forward": 1, "round": 1, "type": "normal", "width": 300},
                    "desc": "[聊天记录]",
                    "extra": f'{json.dumps({"filename":fileid,"tsum":len(msg.messages)})}\n',
                    "meta": {
                        "detail": {
                            "news": [
                                {
                                    "text": f'{forward_node.sender_nick}:{"".join(element.raw_text for element in forward_node.content)}'
                                }
                                for forward_node in msg.messages
                            ],
                            "resid": msg.resid,
                            "source": "群聊的聊天记录",
                            "summary": f"查看{len(msg.messages)}条转发消息",
                            "uniseq": f"{fileid}",
                        }
                    },
                    "prompt": "[聊天记录]",
                    "ver": "0.0.0.5",
                    "view": "contact",
                }
                msg_pb.append(Elems(mini_app=MiniApp(template=b"\x01" + zlib.compress(json.dumps(template).encode()))))
            else:
                raise NotImplementedError
    else:
        audio = msg_chain[0]  # type: Audio
        if audio.id:  # grp
            msg_ptt = Ptt(
                md5=audio.md5,
                name=audio.name,
                size=audio.size,
                file_id=audio.id,
                group_file_key=audio.file_key,
                time=audio.time,
            )
        else:  # friend
            msg_ptt = Ptt.decode(audio.qmsg)
    return RichText(content=msg_pb, ptt=msg_ptt)


async def build_forward_msg(
    forword_msg: MulitMsg,
    forward_func: Callable[..., Coroutine[Any, Any, str]],
    *,
    is_group: bool,
) -> PbMultiMsgTransmit:
    start_seq = random.randint(1000000, 9999999)
    messages = [
        MsgPushBody(
            response_head=(
                ResponseHead(from_uin=node.sender_uin, rsp_grp=Grp(sender_name=node.sender_nick, f5=2))
                if is_group
                else ResponseHead(from_uin=node.sender_uin)
            ),
            content_head=ContentHead(
                type=82 if is_group else 166,
                random=random.randint(100000000, 2147483647),
                seq=seq,
                timestamp=node.timestamp,
                forward=Forward(
                    custom_flag=b"666" if node.sender_nick or node.sender_avatar_url else b"",
                    avatar_url=node.sender_avatar_url,
                ),
            ),
            message=Message(body=await build_message(node.content, forward_func=forward_func)),
        )
        for seq, node in enumerate(forword_msg.messages, start_seq)
    ]
    return PbMultiMsgTransmit(
        items=[
            PbMultiMsgItem(
                file_name="MultiMsg",
                buffer=PbMultiMsgNew(msg=messages),
            )
        ]
    )


# it should be enterpoint
async def _get_mulitmsg_resid(
    client: "Client", forword_msg: MulitMsg, target: str = "", grp_id: Optional[int] = None
) -> str:
    body = await build_forward_msg(
        forword_msg,
        get_resid_func(client, target, grp_id),
        is_group=grp_id is not None,
    )

    packet = await client.send_uni_packet(
        "trpc.group.long_msg_interface.MsgService.SsoSendLongMsg",
        LongMsgRsp.build(gzip.compress(body.encode()), target, grp_id).encode(),
    )
    result = LongMsgResp.decode(packet.data)
    return result.result.resid


def get_resid_func(
    client: "Client", target: str = "", grp_id: Optional[int] = None
) -> Callable[..., Coroutine[Any, Any, str]]:
    async def wrap(forword_msg: MulitMsg):
        return await _get_mulitmsg_resid(client, forword_msg, target, grp_id)

    return wrap
