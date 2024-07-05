import asyncio
import logging
import os

from lagrange.client.client import Client
from lagrange.client.events.group import GroupMessage
from lagrange.client.events.service import ServerKick
from lagrange.client.message.elems import At, Raw, Text
from lagrange.info.app import app_list
from lagrange.info.device import DeviceInfo
from lagrange.info.sig import SigInfo
from lagrange.utils.sign import sign_provider

DEVICE_INFO_PATH = "./device.json"
SIGINFO_PATH = "./sig.bin"


class InfoManager:
    def __init__(self, uin: int, device_info_path: str, sig_info_path: str):
        self.uin: int = uin
        self._device_info_path: str = device_info_path
        self._sig_info_path: str = sig_info_path
        self._device = None
        self._sig_info = None

    @property
    def device(self) -> DeviceInfo:
        assert self._device, "Device not initialized"
        return self._device

    @property
    def sig_info(self) -> SigInfo:
        assert self._sig_info, "SigInfo not initialized"
        return self._sig_info

    def save_all(self):
        with open(self._sig_info_path, "wb") as f:
            f.write(self._sig_info.dump())

        with open(self._device_info_path, "wb") as f:
            f.write(self._device.dump())

        print("device info saved")

    def __enter__(self):
        if os.path.isfile(self._device_info_path):
            with open(self._device_info_path, "rb") as f:
                self._device = DeviceInfo.load(f.read())
        else:
            print(f"{self._device_info_path} not found, generating...")
            self._device = DeviceInfo.generate(self.uin)

        if os.path.isfile(self._sig_info_path):
            with open(self._sig_info_path, "rb") as f:
                self._sig_info = SigInfo.load(f.read())
        else:
            print(f"{self._sig_info_path} not found, generating...")
            self._sig_info = SigInfo.new(8848)
        return self

    def __exit__(self, *_):
        pass


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(name)s[%(levelname)s]: %(message)s"
)


async def heartbeat_task(client: Client):
    while True:
        await client.online.wait()
        await asyncio.sleep(120)
        print(f"{round(await client.sso_heartbeat(True) * 1000, 2)}ms to server")


async def msg_handler(client: Client, event: GroupMessage):
    print(event)
    if event.msg.startswith("114514"):
        p = await client.send_grp_msg([Text("1919810")], event.grp_id)
        await asyncio.sleep(5)
        await client.recall_grp_msg(event.grp_id, p)
    elif event.msg.startswith("imgs"):
        await client.send_grp_msg(
            [
                await client.upload_grp_image(
                    open("98416427_p0.jpg", "rb"), event.grp_id
                )
            ],
            event.grp_id,
        )
    print(f"{event.nickname}({event.grp_name}): {event.msg}")


async def handle_kick(client: "Client", event: "ServerKick"):
    print(f"被服务器踢出：[{event.title}] {event.tips}")
    await client.stop()


async def main():
    uin = int(os.environ.get("LAGRANGE_UIN", "0"))
    sign_url = os.environ.get("LAGRANGE_SIGN_URL", "")

    app = app_list["linux"]

    with InfoManager(uin, DEVICE_INFO_PATH, SIGINFO_PATH) as im:
        client = Client(
            uin,
            app,
            im.device,
            im.sig_info,
            sign_provider(sign_url) if sign_url else None,
        )
        client.events.subscribe(GroupMessage, msg_handler)
        client.events.subscribe(ServerKick, handle_kick)
        client.connect()
        asyncio.create_task(heartbeat_task(client))
        if im.sig_info.d2:
            if not await client.register():
                await client.login()
        else:
            await client.login()
        im.save_all()
        await client.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
