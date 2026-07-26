import asyncio
import os

from lagrange import Lagrange, install_loguru
from lagrange.client.client import Client
from lagrange.client.events.friend import FriendMessage
from lagrange.client.events.group import GroupMessage, GroupSign, GroupReaction, GroupAdminChange
from lagrange.client.events.service import ServerKick
from lagrange.client.message.elems import At, Emoji, ForwardNode, MulitMsg, Quote, Text


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
    elif event.msg.startswith("forward_send"):
        forward_msg = MulitMsg(
            messages=[
                ForwardNode(
                    content=[Text("群合并转发测试节点 1")],
                    sender_uin=client.uin,
                    sender_nick="Lagrange Bot",
                ),
                ForwardNode(
                    content=[Text(f"群合并转发测试节点 2，触发者：{event.nickname or event.uin}")],
                    sender_uin=event.uin,
                    sender_nick=event.nickname or str(event.uin),
                ),
            ]
        )
        seq = await client.send_grp_forward_msg(forward_msg, event.grp_id)
        print(f"group forward send ok: seq={seq}, resid={forward_msg.resid}")
    elif event.msg.startswith("forward_get"):
        resid = event.msg.removeprefix("forward_get").strip()
        if not resid:
            await client.send_grp_msg([Text("用法：forward_get <resid>")], event.grp_id)
        else:
            forward_msg = await client.get_forward_msg(resid, is_group=True)
            print(f"group forward get ok: resid={resid}, nodes={len(forward_msg.messages)}")
            for idx, node in enumerate(forward_msg.messages, 1):
                text = "".join(elem.display for elem in node.content)
                print(f"  node#{idx}: {node.sender_nick}({node.sender_uin}) {node.timestamp}: {text}")

    for elem in event.msg_chain:
        if isinstance(elem, MulitMsg) and elem.resid:
            forward_msg = await client.get_forward_msg(elem.resid, is_group=True)
            print(f"group forward received: file={elem.file_name}, resid={elem.resid}, nodes={len(forward_msg.messages)}")
            for idx, node in enumerate(forward_msg.messages, 1):
                text = "".join(item.display for item in node.content)
                print(f"  node#{idx}: {node.sender_nick}({node.sender_uin}) {node.timestamp}: {text}")
    print(f"{event.nickname}({event.grp_name}): {event.msg}")


async def friend_msg_handler(client: Client, event: FriendMessage):
    if event.msg.startswith("forward_send"):
        forward_msg = MulitMsg(
            messages=[
                ForwardNode(
                    content=[Text("好友合并转发测试节点 1")],
                    sender_uin=client.uin,
                    sender_nick="Lagrange Bot",
                ),
                ForwardNode(
                    content=[Text(f"好友合并转发测试节点 2，触发者：{event.from_uin}")],
                    sender_uin=event.from_uin,
                    sender_nick=str(event.from_uin),
                ),
            ]
        )
        seq = await client.send_friend_forward_msg(forward_msg, event.from_uid)
        print(f"friend forward send ok: seq={seq}, resid={forward_msg.resid}")
    elif event.msg.startswith("forward_get"):
        resid = event.msg.removeprefix("forward_get").strip()
        if not resid:
            await client.send_friend_msg([Text("用法：forward_get <resid>")], event.from_uid)
        else:
            forward_msg = await client.get_forward_msg(resid, is_group=False)
            print(f"friend forward get ok: resid={resid}, nodes={len(forward_msg.messages)}")
            for idx, node in enumerate(forward_msg.messages, 1):
                text = "".join(elem.display for elem in node.content)
                print(f"  node#{idx}: {node.sender_nick}({node.sender_uin}) {node.timestamp}: {text}")

    for elem in event.msg_chain:
        if isinstance(elem, MulitMsg) and elem.resid:
            forward_msg = await client.get_forward_msg(elem.resid, is_group=False)
            print(f"friend forward received: file={elem.file_name}, resid={elem.resid}, nodes={len(forward_msg.messages)}")
            for idx, node in enumerate(forward_msg.messages, 1):
                text = "".join(item.display for item in node.content)
                print(f"  node#{idx}: {node.sender_nick}({node.sender_uin}) {node.timestamp}: {text}")

    print(f"friend {event.from_uin}: {event.msg}")


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
            k = kk.next_key.decode()
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


async def handle_group_admin(client: Client, event: GroupAdminChange):
    user_info = await client.get_user_info(event.uid)
    if event.is_set:
        print(f"{user_info.name} is now an admin")
    else:
        print(f"{user_info.name} is no longer an admin")


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
lag.subscribe(GroupAdminChange, handle_group_admin)


lag.launch()
