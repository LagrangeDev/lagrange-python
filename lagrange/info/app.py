from dataclasses import dataclass
from typing import TypedDict

from .serialize import JsonSerializer


@dataclass
class AppInfo(JsonSerializer):
    os: str
    kernel: str
    vendor_os: str

    current_version: str
    build_version: int
    misc_bitmap: int
    pt_version: str
    pt_os_version: int
    package_name: str
    wtlogin_sdk: str
    package_sign: str
    app_id: int
    sub_app_id: int
    app_id_qrcode: int
    app_client_version: int
    main_sigmap: int
    sub_sigmap: int
    nt_login_type: int


class AppInfoDict(TypedDict):
    linux: AppInfo
    macos: AppInfo
    windows: AppInfo


app_list: AppInfoDict = {
    "linux": AppInfo(
        os="Linux",
        kernel="Linux",
        vendor_os="linux",
        current_version="3.2.10-25765",
        build_version=25765,
        misc_bitmap=32764,
        pt_version="2.0.0",
        pt_os_version=19,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        package_sign="V1_LNX_NQ_3.1.2-13107_RDM_B",
        app_id=1600001615,
        sub_app_id=537234773,
        app_id_qrcode=13697054,
        app_client_version=13172,
        main_sigmap=169742560,
        sub_sigmap=0,
        nt_login_type=1,
    ),
    "macos": AppInfo(
        os="Mac",
        kernel="Darwin",
        vendor_os="mac",
        current_version="6.9.20-17153",
        build_version=17153,
        misc_bitmap=32764,
        pt_version="2.0.0",
        pt_os_version=23,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        package_sign="V1_MAC_NQ_6.9.20-17153_RDM_B",
        app_id=1600001602,
        sub_app_id=537162356,
        app_id_qrcode=537162356,
        app_client_version=13172,
        main_sigmap=169742560,
        sub_sigmap=0,
        nt_login_type=5,
    ),
    "windows": AppInfo(
        os="Windows",
        kernel="Windows_NT",
        vendor_os="win32",
        current_version="9.9.2-15962",
        build_version=15962,
        pt_version="2.0.0",
        misc_bitmap=32764,
        pt_os_version=23,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        package_sign="V1_WIN_NQ_9.9.2-15962_RDM_B",
        app_id=1600001604,
        sub_app_id=537138217,
        app_id_qrcode=537138217,
        app_client_version=13172,
        main_sigmap=169742560,
        sub_sigmap=0,
        nt_login_type=5
    )
}
