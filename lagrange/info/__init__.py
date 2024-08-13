import os
from pathlib import Path
from typing import Union

from .app import AppInfo
from .device import DeviceInfo
from .sig import SigInfo

from ..utils.log import log

__all__ = ["DeviceInfo", "AppInfo", "SigInfo", "InfoManager"]


class InfoManager:
    def __init__(
        self,
        uin: int,
        device_info_path: Union[str, os.PathLike[str]],
        sig_info_path: Union[str, os.PathLike[str]],
        auto_save=True,
    ):
        self.uin: int = uin
        self._device_info_path = Path(device_info_path)
        self._sig_info_path = Path(sig_info_path)
        self._device = None
        self._sig_info = None
        self.auto_save = auto_save

    @property
    def device(self) -> DeviceInfo:
        assert self._device, "Device not initialized"
        return self._device

    @property
    def sig_info(self) -> SigInfo:
        assert self._sig_info, "SigInfo not initialized"
        return self._sig_info

    def renew_sig_info(self):
        self._sig_info = SigInfo.new()

    def save_all(self):
        with self._sig_info_path.open("wb") as f:
            f.write(self.sig_info.dump())

        with self._device_info_path.open("wb") as f:
            f.write(self.device.dump())

        log.root.success("device & sig_info saved")

    def __enter__(self):
        if self._device_info_path.is_file():
            with self._device_info_path.open("rb") as f:
                self._device = DeviceInfo.load(f.read())
            log.root.success(f"{self._device_info_path} loaded")
        else:
            log.root.info(f"{self._device_info_path} not found, generating...")
            self._device = DeviceInfo.generate(self.uin)

        if self._sig_info_path.is_file():
            with self._sig_info_path.open("rb") as f:
                self._sig_info = SigInfo.load(f.read())
            log.root.success(f"{self._sig_info_path} loaded")
        else:
            log.root.info(f"{self._sig_info_path} not found, generating...")
            self._sig_info = SigInfo.new(8848)
        return self

    def __exit__(self, *_):
        if self.auto_save:
            self.save_all()
        return
