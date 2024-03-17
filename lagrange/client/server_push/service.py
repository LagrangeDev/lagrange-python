from lagrange.pb.status.kick import KickNT

from ..events.service import ServerKick
from ..wtlogin.sso import SSOPacket
from .binder import push_handler


@push_handler.subscribe("trpc.qq_new_tech.status_svc.StatusService.KickNT")
async def server_kick(sso: SSOPacket):
    ev = KickNT.decode(sso.data)
    return ServerKick(tips=ev.tips, title=ev.title)
