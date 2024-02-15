import asyncio
from lagrange.client.base import BaseClient
from lagrange.info.app import app_list
from lagrange.info.device import DeviceInfo
from lagrange.info.sig import SigInfo


async def main():
    uin = 0
    client = BaseClient(uin, app_list['linux'], DeviceInfo.generate(uin), SigInfo.new(500000))
    client.connect()
    await client.fetch_qrcode()
    await client.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
