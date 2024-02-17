import asyncio
from lagrange.client.base import BaseClient
from lagrange.info.app import app_list
from lagrange.info.device import DeviceInfo
from lagrange.info.sig import SigInfo


async def main():
    uin = 0
    client = BaseClient(uin, app_list['linux'], DeviceInfo.generate(uin), SigInfo.new(8848))
    client.connect()
    png, _link = await client.fetch_qrcode()
    print("save to qrcode.png")
    with open("qrcode.png", "wb") as f:
        f.write(png)
    await client.qrcode_login(3)
    await client.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
