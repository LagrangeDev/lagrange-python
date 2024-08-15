import asyncio
import os

from lagrange import Lagrange, install_loguru
from lagrange.client.client import Client
from lagrange.client.events.group import GroupMessage, GroupSign, GroupReaction
from lagrange.client.events.service import ServerKick
from lagrange.client.message.elems import At, Text, Quote, Emoji


async def msg_handler(client: Client, event: GroupMessage):
    # print(event)
    if event.msg.startswith("114514"):
        msg_seq = await client.send_grp_msg(
            [At.build(event), Text("1919810")], event.grp_id
        )
        await asyncio.sleep(5)
        await client.recall_grp_msg(event.grp_id, msg_seq)
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


async def handle_grp_sign(client: "Client", event: "GroupSign"):
    a = "闲着没事爱打卡，可以去找个班上"
    k = None
    uid = None
    while True:
        kk = await client.get_grp_members(event.grp_id, k)
        for m in kk.body:
            if m.account.uin == event.uin:
                uid = m.account.uid
                break
        if uid:
            break
        if kk.next_key:
            k = kk.next_key
        else:
            raise ValueError(f"cannot find member: {event.uin}")

    await client.send_grp_msg(
        [At(f"@{event.nickname} ", event.uin, uid), Text(a)], event.grp_id
    )


async def handle_group_reaction(client: "Client", event: "GroupReaction"):
    msg = (await client.get_grp_msg(event.grp_id, event.seq))[0]
    mi = (await client.get_grp_member_info(event.grp_id, event.uid)).body[0]
    if event.is_emoji:
        e = Text(chr(event.emoji_id))
    else:
        e = Emoji(event.emoji_id)
    if event.is_increase:
        m = "给你点了"
    else:
        m = "取消了"
    await client.send_grp_msg(
        [Quote.build(msg), Text(f"{mi.name.string if mi.name else mi.nickname}{m}"), e],
        event.grp_id,
    )


lag = Lagrange(
    int(os.environ.get("LAGRANGE_UIN", "0")),
    "linux",
    os.environ.get("LAGRANGE_SIGN_URL", "")
)
install_loguru()  # optional, for better logging
lag.log.set_level("DEBUG")

lag.subscribe(GroupMessage, msg_handler)
lag.subscribe(ServerKick, handle_kick)
lag.subscribe(GroupSign, handle_grp_sign)
lag.subscribe(GroupReaction, handle_group_reaction)


lag.launch()
