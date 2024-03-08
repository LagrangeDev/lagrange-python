from lagrange.utils.binary.protobuf import proto_encode
from lagrange.info import AppInfo, DeviceInfo
from lagrange.utils.log import logger
from lagrange.pb.wtlogin.register import PBRegisterRequest, PBRegisterResponse


# trpc.qq_new_tech.status_svc.StatusService.Register
def build_register_request(app: AppInfo, device: DeviceInfo) -> bytes:
    return PBRegisterRequest.build(app, device).encode()


# trpc.qq_new_tech.status_svc.StatusService.SsoHeartBeat
def build_sso_heartbeat_request() -> bytes:
    return proto_encode({1: 1})


def parse_register_response(response: bytes) -> bool:
    pb = PBRegisterResponse.decode(response)
    if pb.message == "register success":
        return True
    logger.network.error("register fail, reason: %s", pb.message)
    return False
