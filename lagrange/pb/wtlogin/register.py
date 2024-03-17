from lagrange.info import AppInfo, DeviceInfo
from lagrange.utils.binary.protobuf import ProtoField, ProtoStruct


class _DeviceInfo(ProtoStruct):
    device_name: str = ProtoField(1)
    vendor_os: str = ProtoField(2)
    system_kernel: str = ProtoField(3)
    vendor_name: str = ProtoField(4, "")
    vendor_os_lower: str = ProtoField(5)


class PBRegisterRequest(ProtoStruct):
    guid: str = ProtoField(1)
    field_2: int = ProtoField(2, 0)
    current_version: str = ProtoField(3)
    field_4: int = ProtoField(4, 0)
    locale_id: int = ProtoField(5, 2052)
    device_info: _DeviceInfo = ProtoField(6)
    set_mute: int = ProtoField(7, 0)  # ?
    register_vendor_type: int = ProtoField(8, 0)  # ?
    register_type: int = ProtoField(9, 1)

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
    message: str = ProtoField(2)
    timestamp: int = ProtoField(3)
