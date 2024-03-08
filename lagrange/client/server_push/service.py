from lagrange.pb.status.kick import KickNT

from .binder import push_handler
from ..wtlogin.sso import SSOPacket
from ..events.service import ServerKick


@push_handler.subscribe("trpc.qq_new_tech.status_svc.StatusService.KickNT")
async def server_kick(sso: SSOPacket):
    ev = KickNT.decode(sso.data)
    return ServerKick(
        tips=ev.tips,
        title=ev.title
    )
