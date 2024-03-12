from lagrange.client.message.decoder import parse_grp_msg
from lagrange.utils.binary.reader import Reader
from lagrange.utils.binary.protobuf import proto_decode
from lagrange.utils.operator import unpack_dict

from .log import logger
from .binder import push_handler
from ..events.group import GroupRecall, GroupMuteMember, GroupMemberJoined, GroupMemberQuit, GroupMemberJoinRequest
from ..wtlogin.sso import SSOPacket

from lagrange.pb.message.msg_push import MsgPush
from lagrange.pb.status.group import MemberChanged, MemberJoinRequest, MemberInviteRequest


@push_handler.subscribe("trpc.msg.olpush.OlPushService.MsgPush")
async def msg_push_handler(sso: SSOPacket):
    pkg = MsgPush.decode(sso.data).body
    typ = pkg.content_head.type
    sub_typ = pkg.content_head.sub_type

    logger.debug("msg_push received, type:{}".format(typ))
    if typ == 82:  # grp msg
        return parse_grp_msg(pkg)
    elif typ == 166:  # frd msg
        pass
    elif typ == 33:  # member joined
        pb = MemberChanged.decode(pkg.message.buf2)
        return GroupMemberJoined(
            uin=pb.uin,
            uid=pb.uid,
            join_type=pb.join_type
        )
    elif typ == 34:  # member exit
        pb = MemberChanged.decode(pkg.message.buf2)
        return GroupMemberQuit(
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
            _key=pb.field_9,
            src=pb.src,
            answer=pb.request_field
        )
    elif typ == 525:
        pb = MemberInviteRequest.decode(pkg.message.buf2)
        print(pb)
        if pb.cmd == 87:
            inn = pb.info.inner
            return GroupMemberJoinRequest(
                grp_id=inn.grp_id,
                uid=inn.uid,
                _key=b"",
                src=0,
                invitor_uid=inn.invitor_uid
            )
    elif typ == 0x210:  # frd event
        print(210, pkg)
    elif typ == 0x2dc:  # grp event, 732
        if sub_typ == 20:  # nudget(grp_id only)
            pass
        if sub_typ == 17:  # recall
            reader = Reader(pkg.message.buf2)
            grp_id = reader.read_u32()
            reader.read_u8()  # reserve
            in_pb = unpack_dict(
                proto_decode(reader.read_bytes_with_length("u16", False)),
                "11"
            )

            info = in_pb[3]
            return GroupRecall(
                uid=info[6],
                seq=info[1],
                time=info[2],
                rand=info[3],
                grp_id=grp_id,
                suffix=unpack_dict(in_pb, "9.2", "").strip()
            )
        elif sub_typ == 12:  # mute
            info = proto_decode(pkg.message.buf2)
            return GroupMuteMember(
                grp_id=info[1],
                operator_uid=info[4],
                target_uid=unpack_dict(info, "5.3.1", ""),
                duration=unpack_dict(info, "5.3.2")
            )
        else:
            print("unknown subtype", sub_typ, pkg.message.buf2.hex())
    else:
        print("unknown type", typ, pkg.message.buf2.hex())