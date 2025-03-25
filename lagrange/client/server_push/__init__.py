from .binder import PushDeliver
from .msg import msg_push_handler
from .service import (
    server_kick_handler,
    server_info_sync_handler,
    server_push_param_handler,
    server_push_req_handler
)


def bind_services(pd: PushDeliver):
    pd.subscribe("trpc.msg.olpush.OlPushService.MsgPush", msg_push_handler)

    pd.subscribe("trpc.qq_new_tech.status_svc.StatusService.KickNT", server_kick_handler)
    pd.subscribe("trpc.msg.register_proxy.RegisterProxy.InfoSyncPush", server_info_sync_handler)
    pd.subscribe("trpc.msg.register_proxy.RegisterProxy.PushParams", server_push_param_handler)
    pd.subscribe("ConfigPushSvc.PushReq", server_push_req_handler)
