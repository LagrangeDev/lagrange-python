from lagrange.info import AppInfo, DeviceInfo
from lagrange.utils.binary.protobuf import proto_encode
from lagrange.utils.log import log
from lagrange.pb.login.register import (
    PBRegisterRequest,
    PBRegisterResponse,
    PBSsoInfoSyncRequest,
    PBSsoInfoSyncResponse,
)


# trpc.qq_new_tech.status_svc.StatusService.Register
def build_register_request(app: AppInfo, device: DeviceInfo) -> bytes:
    return PBRegisterRequest.build(app, device).encode()


# trpc.msg.register_proxy.RegisterProxy.SsoInfoSync
def build_sso_info_sync(app: AppInfo, device: DeviceInfo) -> bytes:
    return PBSsoInfoSyncRequest.build(app, device).encode()


# trpc.qq_new_tech.status_svc.StatusService.SsoHeartBeat
def build_sso_heartbeat_request() -> bytes:
    return proto_encode({1: 1})


def parse_register_response(response: bytes) -> bool:
    pb = PBRegisterResponse.decode(response)
    if pb.message == "register success":
        return True
    log.network.error("register fail, reason: %s", pb.message)
    return False


def parse_sso_info_sync_rsp(response: bytes) -> bool:
    pb = PBSsoInfoSyncResponse.decode(response)
    if pb.reg_rsp:
        if pb.reg_rsp.message == "register success":
            return True
        else:
            log.network.error("register fail, reason: %s", pb.reg_rsp.message)
    else:
        log.network.error("register fail, reason: WrongRsp")
    return False
