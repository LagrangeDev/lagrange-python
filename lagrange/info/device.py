import platform
from dataclasses import dataclass
from hashlib import md5
from typing import Union

from .serialize import JsonSerializer


@dataclass
class DeviceInfo(JsonSerializer):
    guid: str
    device_name: str
    system_kernel: str
    kernel_version: str

    @classmethod
    def generate(cls, uin: Union[str, int]) -> "DeviceInfo":
        if isinstance(uin, int):
            uin = md5(str(uin).encode()).hexdigest()

        return DeviceInfo(
            guid=uin,
            device_name=f"Lagrange-{md5(uin.encode()).digest()[:4].hex().upper()}",
            system_kernel=f"{platform.system()} {platform.version()}",
            kernel_version=platform.version(),
        )
