import json
import re

from lagrange.client.message.decoder import parse_grp_msg
from lagrange.utils.binary.reader import Reader
from lagrange.utils.binary.protobuf import proto_decode
from lagrange.utils.operator import unpack_dict

from .log import logger
from .binder import push_handler
from ..events.group import (
    GroupRecall,
    GroupMuteMember,
    GroupMemberJoined,
    GroupMemberQuit,
    GroupMemberJoinRequest,
    GroupMemberGotSpecialTitle,
    GroupNameChanged,
)
from ..wtlogin.sso import SSOPacket

from lagrange.pb.message.msg_push import MsgPush
from lagrange.pb.status.group import (
    MemberChanged,
    MemberJoinRequest,
    MemberInviteRequest,
    MemberRecallMsg,
    GroupSub16Head,
    MemberGotTitleBody,
    GroupRenamedBody
)


@push_handler.subscribe("trpc.msg.olpush.OlPushService.MsgPush")
async def msg_push_handler(sso: SSOPacket):
    pkg = MsgPush.decode(sso.data).body
    typ = pkg.content_head.type
    sub_typ = pkg.content_head.sub_type

    logger.debug("msg_push received, type: {}.{}".format(typ, sub_typ))
    if typ == 82:  # grp msg
        return parse_grp_msg(pkg)
    elif typ == 166:  # frd msg
        pass
    elif typ == 33:  # member joined
        pb = MemberChanged.decode(pkg.message.buf2)
        return GroupMemberJoined(
            grp_id=pkg.response_head.from_uin,
            uin=pb.uin,
            uid=pb.uid,
            join_type=pb.join_type
        )
    elif typ == 34:  # member exit
        pb = MemberChanged.decode(pkg.message.buf2)
        return GroupMemberQuit(
            grp_id=pkg.response_head.from_uin,
            uin=pb.uin,
            uid=pb.uid,
            operator_uid=pb.operator_uid,
            exit_type=pb.exit_type
        )
    elif typ == 84:
        pb = MemberJoinRequest.decode(pkg.message.buf2)
        return GroupMemberJoinRequest(
            grp_id=pb.grp_id,
            uid=pb.uid,
            answer=pb.request_field
        )
    elif typ == 525:
        pb = MemberInviteRequest.decode(pkg.message.buf2)
        if pb.cmd == 87:
            inn = pb.info.inner
            return GroupMemberJoinRequest(
                grp_id=inn.grp_id,
                uid=inn.uid,
                invitor_uid=inn.invitor_uid
            )
    elif typ == 0x210:  # frd event
        print(210, pkg)
    elif typ == 0x2dc:  # grp event, 732
        if sub_typ == 20:  # nudget(grp_id only)
            return
        elif sub_typ == 16:  # rename and special_title
            reader = Reader(pkg.message.buf2)
            grp_id = reader.read_u32()
            reader.read_u8()  # reserve
            pb = GroupSub16Head.decode(
                reader.read_bytes_with_length("u16", False)
            )
            if pb.flag == 6:  # special_title
                body = MemberGotTitleBody.decode(pb.body)
                for el in re.findall(r"<(\{.*?})>", body.string):
                    el = json.loads(el)
                    if el["cmd"] == 1:
                        title = el["text"]
                        url = el["data"]
                        break
                else:
                    raise ValueError("cannot find special_title and url")
                return GroupMemberGotSpecialTitle(
                    grp_id=grp_id,
                    member_uin=body.member_uin,
                    special_title=title,
                    _detail_url=url
                )
            elif pb.flag == 12:  # renamed
                body = GroupRenamedBody.decode(pb.body)
                return GroupNameChanged(
                    grp_id=grp_id,
                    name_new=body.grp_name,
                    timestamp=pb.timestamp,
                    operator_uid=pb.operator_uid
                )
            else:
                raise ValueError(f"Unknown subtype_12 flag: {pb.flag}")
        elif sub_typ == 17:  # recall
            reader = Reader(pkg.message.buf2)
            grp_id = reader.read_u32()
            reader.read_u8()  # reserve
            pb = MemberRecallMsg.decode(
                reader.read_bytes_with_length("u16", False)
            )

            info = pb.body.info
            return GroupRecall(
                uid=info.uid,
                seq=info.seq,
                time=info.time,
                rand=info.rand,
                grp_id=grp_id,
                suffix=pb.body.extra.suffix.strip() if pb.body.extra else ""
            )
        elif sub_typ == 12:  # mute
            info = proto_decode(pkg.message.buf2)
            return GroupMuteMember(
                grp_id=info[1],
                operator_uid=info[4].decode(),
                target_uid=unpack_dict(info, "5.3.1", b"").decode(),
                duration=unpack_dict(info, "5.3.2")
            )
        else:
            logger.debug("unknown sub_type %d: %s" % (
                sub_typ, pkg.message.buf2.hex() if getattr(pkg.message, "buf2", None) else pkg
            ))
    else:
        logger.debug("unknown type %d: %s" % (
            sub_typ, pkg.message.buf2.hex() if getattr(pkg.message, "buf2", None) else pkg
        ))
