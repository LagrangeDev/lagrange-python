from .binder import PushDeliver
from .msg import msg_push_handler
from .service import server_kick_handler


def bind_services(pd: PushDeliver):
    pd.subscribe("trpc.msg.olpush.OlPushService.MsgPush", msg_push_handler)
    pd.subscribe(
        "trpc.qq_new_tech.status_svc.StatusService.KickNT", server_kick_handler
    )
