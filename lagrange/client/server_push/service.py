from lagrange.pb.status.kick import KickNT

from ..events.service import ServerKick
from ..wtlogin.sso import SSOPacket


async def server_kick_handler(_, sso: SSOPacket):
    ev = KickNT.decode(sso.data)
    return ServerKick(tips=ev.tips, title=ev.title)
