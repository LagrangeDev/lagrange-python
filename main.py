import asyncio
from lagrange.client.base import BaseClient
from lagrange.info.app import app_list
from lagrange.info.device import DeviceInfo
from lagrange.info.sig import SigInfo


async def main():
    uin = 0
    pwd = "<PASSWORD>"
    client = BaseClient(uin, app_list['linux'], DeviceInfo.generate(uin), SigInfo.new(8848))
    client.connect()
    await client._key_exchange()
    print(f"{round(await client.sso_heartbeat(True) * 1000, 2)}ms")
    if uin:
        await client.password_login(pwd)
        it = input("ticket?->")
        ir = input("rand_str?->")
        client._sig.captcha_info[0] = it
        client._sig.captcha_info[1] = ir
        await client.password_login(pwd)
    else:
        png, _link = await client.fetch_qrcode()
        print("save to qrcode.png")
        with open("qrcode.png", "wb") as f:
            f.write(png)
        await client.qrcode_login(3)
    await client.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
