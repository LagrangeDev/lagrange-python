from lagrange.client.message.decoder import parse_grp_msg
from lagrange.utils.binary.protobuf import proto_decode
from lagrange.utils.operator import unpack_dict

from .log import logger
from .binder import push_handler
from ..wtlogin.sso import SSOPacket


@push_handler.subscribe("trpc.msg.olpush.OlPushService.MsgPush")
async def msg_push_handler(sso: SSOPacket):
    pb = proto_decode(sso.data)
    typ = unpack_dict(pb, "1.2.1")

    logger.debug("msg_push received, type:{}".format(typ))
    if typ == 82:  # grp msg
        return parse_grp_msg(pb[1])
    elif typ == 166:  # frd msg
        pass
    elif typ == 0x2dc:  # grp event, 732
        sub_typ = unpack_dict(pb, "1.2.2")
        print(pb)
        if sub_typ == 17:  # recall
            pass
        elif sub_typ == 12:  # mute
            pass
