from lagrange.info import AppInfo, DeviceInfo
from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class _DeviceInfo(ProtoStruct):
    device_name: str = proto_field(1)
    vendor_os: str = proto_field(2)
    system_kernel: str = proto_field(3)
    vendor_name: str = proto_field(4, default="")
    vendor_os_lower: str = proto_field(5)


class PBRegisterRequest(ProtoStruct):
    guid: str = proto_field(1)
    field_2: int = proto_field(2, default=0)
    current_version: str = proto_field(3)
    field_4: int = proto_field(4, default=0)
    locale_id: int = proto_field(5, default=2052)
    device_info: _DeviceInfo = proto_field(6)
    set_mute: int = proto_field(7, default=0)  # ?
    register_vendor_type: int = proto_field(8, default=0)  # ?
    register_type: int = proto_field(9, default=1)

    @classmethod
    def build(cls, app: AppInfo, device: DeviceInfo) -> "PBRegisterRequest":
        return cls(
            guid=device.guid.upper(),
            current_version=app.current_version,
            device_info=_DeviceInfo(
                device_name=device.device_name,
                vendor_os=app.vendor_os.capitalize(),
                system_kernel=device.system_kernel,
                vendor_os_lower=app.vendor_os,
            ),
        )


class PBRegisterResponse(ProtoStruct):
    message: str = proto_field(2)
    timestamp: int = proto_field(3)
