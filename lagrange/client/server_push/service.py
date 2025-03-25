import os
import datetime

from lagrange.pb.status.kick import KickNT
from lagrange.pb.login.register import PBSsoInfoSyncPush, PBServerPushParams

from ..events.service import ServerKick
from ..wtlogin.sso import SSOPacket

DBG_EN = bool(os.environ.get("PUSH_DEBUG", False))

async def server_kick_handler(_, sso: SSOPacket):
    ev = KickNT.decode(sso.data)
    return ServerKick(tips=ev.tips, title=ev.title)


async def server_info_sync_handler(_, sso: SSOPacket):
    if not DBG_EN:
        return
    ev = PBSsoInfoSyncPush.decode(sso.data)
    if ev.cmd_type == 5:  # grp info
        print("GroupInfo Sync:")
        for i in ev.grp_info:
            print(
                "%i(%s): lostsync: %i, time: %s" % (
                    i.grp_id, i.grp_name, i.last_msg_seq - i.last_msg_seq_read,
                    datetime.datetime.fromtimestamp(i.last_msg_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                )
            )
    elif ev.cmd_type == 2:
        print("MsgPush Sync:")
        for i in ev.grp_msgs.inner:
            print(
                "%i msgs(%i->%i) in %i, time: %s" %(
                    len(i.msgs), i.start_seq, i.end_seq, i.grp_id,
                    datetime.datetime.fromtimestamp(i.last_msg_time).strftime("%Y-%m-%d %H:%M:%S")
                )
            )
        print("EventPush Sync:")
        for i in ev.sys_events.inner:
            print(
                "%i events in %i, time: %s" % (
                    len(i.events), i.grp_id,
                    datetime.datetime.fromtimestamp(i.last_evt_time).strftime("%Y-%m-%d %H:%M:%S")
                )
            )
    else:
        print(f"Unknown cmd_type: {ev.cmd_type}({ev.f4})")
    print("END")


async def server_push_param_handler(_, sso: SSOPacket):
    if not DBG_EN:
        return
    print("Server Push Params:")
    ev = PBServerPushParams.decode(sso.data)
    for dev in ev.online_devices:
        print(f"Device:{dev.device_name} on {dev.os_name} Platform, sub_id: {dev.sub_id}")
    print("end")


async def server_push_req_handler(_, sso: SSOPacket):
    """
    JCE packet, ignore
    """
    return None