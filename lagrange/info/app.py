import re
from dataclasses import dataclass
from typing import TypedDict, TypeVar, Union

from .serialize import JsonSerializer


_T = TypeVar("_T", bound=dict[str, Union[int, str]])
_trans_map = {
    "SsoVersion": "pt_os_version",
    "WtLoginSdk": "wtlogin_sdk",
    "AppIdQrCode": "app_id_qrcode",
    "MainSigMap": "main_sigmap",
    "SubSigMap": "sub_sigmap",
}

def _translate_appinfo(s: _T) -> _T:
    out: _T = {}
    for k, v in s.items():
        if k in _trans_map:
            out[_trans_map[k]] = v
        else:
            k = re.sub(
                r"([A-Z])([^A-Z]+)",
                r"_\1\2",
                k
            ).lstrip("_").lower()
            out[k] = v
    return out


@dataclass
class AppInfo(JsonSerializer):
    os: str
    kernel: str
    vendor_os: str

    current_version: str
    # build_version: int
    misc_bitmap: int
    pt_version: str
    pt_os_version: int
    package_name: str
    wtlogin_sdk: str
    app_id: int
    sub_app_id: int
    app_id_qrcode: int
    app_client_version: int
    main_sigmap: int
    sub_sigmap: int
    nt_login_type: int
    qua: str

    @property
    def build_version(self) -> int:
        return int(self.current_version.split("-")[1])

    @property
    def package_sign(self) -> str:
        # QUA?
        if self.os == "Windows":
            kernel = "WIN"
        elif self.os == "Linux":
            kernel = "LNX"
        elif self.os == "Mac":
            kernel = "MAC"
        else:
            raise NotImplementedError(self.os)
        return f"V1_{kernel}_NQ_{self.current_version}_RDM_B"

    @classmethod
    def load_custom(cls, d: _T) -> "AppInfo":
        return cls(**_translate_appinfo(d))


class AppInfoDict(TypedDict):
    linux: AppInfo
    macos: AppInfo
    windows: AppInfo


app_list: AppInfoDict = {
    "linux": AppInfo(
        os="Linux",
        kernel="Linux",
        vendor_os="linux",
        current_version="3.2.26-46494",
        misc_bitmap=32764,
        pt_version="2.0.0",
        pt_os_version=19,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        app_id=1600001615,
        sub_app_id=537345891,
        app_id_qrcode=13697054,
        app_client_version=46494,
        main_sigmap=169742560,
        sub_sigmap=0,
        nt_login_type=1,
        qua="V1_LNX_NQ_3.2.26_46494_GW_B",
    ),
    "macos": AppInfo(
        os="Mac",
        kernel="Darwin",
        vendor_os="mac",
        current_version="6.9.23-20139",
        misc_bitmap=12058620,
        pt_version="2.0.0",
        pt_os_version=23,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        app_id=1600001602,
        sub_app_id=537200848,
        app_id_qrcode=537162356,
        app_client_version=13172,
        main_sigmap=169732560,
        sub_sigmap=0,
        nt_login_type=5,
        qua="",
    ),
    "windows": AppInfo(
        os="Windows",
        kernel="Windows_NT",
        vendor_os="win32",
        current_version="9.9.19-35184",
        pt_version="2.0.0",
        misc_bitmap=12058620,
        pt_os_version=23,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        app_id=1600001604,
        sub_app_id=537291048,
        app_id_qrcode=537138217,
        app_client_version=35184,
        main_sigmap=169732560,
        sub_sigmap=0,
        nt_login_type=5,
        qua="",
    )
}
