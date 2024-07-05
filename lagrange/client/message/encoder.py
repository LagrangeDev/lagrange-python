import struct
import zlib
from typing import List, Optional

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
)
from lagrange.pb.message.rich_text.elems import Text as PBText

from .elems import (
    At,
    AtAll,
    Audio,
    Emoji,
    Image,
    Json,
    Quote,
    Raw,
    Reaction,
    Service,
    Text,
    Poke,
    MarketFace,
)
from .types import Element


def build_message(msg_chain: List[Element], compatible=True) -> RichText:
    if not msg_chain:
        raise ValueError("Message chain is empty")
    msg_pb: List[Elems] = []
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
                            attr6_buf=struct.pack(
                                "!xb3xbbI2x", 1, len(msg.text), 0, msg.uin
                            ),
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
                                attr6_buf=struct.pack(
                                    "!xb3xbbI2x", 1, len(text), 0, msg.uin
                                ),
                                pb_reserved={3: 2, 4: 0, 5: 0, 9: msg.uid, 11: 0},
                            )
                        )
                    )
            elif isinstance(msg, Emoji):
                msg_pb.append(Elems(face=Face(index=msg.id)))
            elif isinstance(msg, Json):
                msg_pb.append(
                    Elems(mini_app=MiniApp(template=b"\x01" + zlib.compress(msg.raw)))
                )
            elif isinstance(msg, Image):
                if msg.id:  # customface
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
                                    display_name=msg.text
                                    or ("[动画表情]" if msg.is_emoji else "[图片]"),
                                ),
                            )
                        )
                    )
                else:
                    msg_pb.append(
                        Elems(not_online_image=NotOnlineImage.decode(msg.qmsg))
                    )
            elif isinstance(msg, Service):
                msg_pb.append(
                    Elems(
                        rich_msg=RichMsg(
                            template=b"\x01" + zlib.compress(msg.raw), service_id=msg.id
                        )
                    )
                )
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
                            name=msg.text,
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
