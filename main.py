import asyncio
import os

from lagrange import Lagrange
from lagrange.client.client import Client
from lagrange.client.events.group import GroupMessage
from lagrange.client.events.service import ServerKick
from lagrange.client.message.elems import At, Raw, Text


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


lag = Lagrange(
    int(os.environ.get("LAGRANGE_UIN", "0")),
    "linux",
    os.environ.get("LAGRANGE_SIGN_URL", "")
)
lag.log.set_level("DEBUG")
lag.subscribe(GroupMessage, msg_handler)
lag.subscribe(ServerKick, handle_kick)


lag.launch()
