from lagrange.client.message.decoder import parse_grp_msg
from lagrange.utils.binary.reader import Reader
from lagrange.utils.binary.protobuf import proto_decode
from lagrange.utils.operator import unpack_dict

from .log import logger
from .binder import push_handler
from ..events.group import GroupRecall, GroupMuteMember
from ..wtlogin.sso import SSOPacket


@push_handler.subscribe("trpc.msg.olpush.OlPushService.MsgPush")
async def msg_push_handler(sso: SSOPacket):
    pb = proto_decode(sso.data)[1]
    typ = unpack_dict(pb, "2.1")
    sub_typ = unpack_dict(pb, "2.2", 0)

    logger.debug("msg_push received, type:{}".format(typ))
    if typ == 82:  # grp msg
        return parse_grp_msg(pb)
    elif typ == 166:  # frd msg
        pass
    elif typ == 0x210:
        print(210, pb)
    elif typ == 0x2dc:  # grp event, 732
        if sub_typ == 20:  # nudget(grp_id only)
            pass
        if sub_typ == 17:  # recall
            reader = Reader(unpack_dict(pb, "3.2"))
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
            info = unpack_dict(pb, "3.2")
            return GroupMuteMember(
                grp_id=info[1],
                operator_uid=info[4],
                target_uid=unpack_dict(info, "5.3.1", ""),
                duration=unpack_dict(info, "5.3.2")
            )
