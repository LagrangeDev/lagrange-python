import asyncio
import os

from lagrange import Lagrange, install_loguru
from lagrange.client.client import Client
from lagrange.client.events.friend import FriendMessage, FriendRequest
from lagrange.client.events.group import GroupMessage, GroupSign, GroupReaction, GroupAdminChange
from lagrange.client.events.service import ServerKick
from lagrange.client.message.elems import At, Emoji, ForwardNode, MulitMsg, Quote, Text, Video


async def msg_handler(client: Client, event: GroupMessage):
    # print(event)
    if event.msg.startswith("114514"):
        msg_seq = await client.send_grp_msg([At.build(event), Text("1919810")], event.grp_id)
        await asyncio.sleep(5)
        await client.recall_grp_msg(event.grp_id, msg_seq)
    elif event.msg.startswith("imgs"):
        await client.send_grp_msg(
            [await client.upload_grp_image(open("98416427_p0.jpg", "rb"), event.grp_id)],
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

    elif event.msg.startswith("like_me"):
        resp = await client.friend_like(event.uid, 2)
        print(resp)
    elif event.msg.startswith("我要当管理"):
        await client.set_grp_admin(grp_id=event.grp_id, uid=event.uid, is_set=True)
    elif event.msg.startswith("我不要管理了"):
        await client.set_grp_admin(grp_id=event.grp_id, uid=event.uid, is_set=False)
    elif event.msg.startswith("叫我"):
        name = event.msg.removeprefix("叫我")
        await client.rename_grp_member(grp_id=event.grp_id, target_uid=event.uid, name=name)
    elif event.msg.startswith("头衔"):
        title = event.msg.removeprefix("头衔")
        await client.set_grp_special_title(grp_id=event.grp_id, target_uid=event.uid, title=title)

    for elem in event.msg_chain:
        if isinstance(elem, MulitMsg) and elem.resid:
            forward_msg = await client.get_forward_msg(elem.resid, is_group=True)
            print(
                f"group forward received: file={elem.file_name}, resid={elem.resid}, nodes={len(forward_msg.messages)}"
            )
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
    elif event.msg.startswith("get"):
        info = await client.get_friend_msg(event.from_uid, event.seq)
        await client.send_friend_msg([Text(repr(info))], event.from_uid)
    elif event.msg.startswith("recall"):
        seq = await client.send_friend_msg([Text("114514")], event.from_uid)
        await asyncio.sleep(3)
        await client.recall_friend_msg(event.from_uid, seq)
        print(f"[recall] ok seq={seq}")

    for elem in event.msg_chain:
        if isinstance(elem, MulitMsg) and elem.resid:
            forward_msg = await client.get_forward_msg(elem.resid, is_group=False)
            print(
                f"friend forward received: file={elem.file_name}, resid={elem.resid}, nodes={len(forward_msg.messages)}"
            )
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

    await client.send_grp_msg([At(f"@{event.nickname} ", event.uin, uid), Text(a)], event.grp_id)


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


# async def handle_friend_req(client: Client, event: FriendRequest):
#     print("加好友？和我吗？")
#     await client.set_friend_request(target_uid=event.from_uid, accept=True)

lag = Lagrange(int(os.environ.get("LAGRANGE_UIN", "0")), "linux", os.environ.get("LAGRANGE_SIGN_URL", ""))
install_loguru()  # optional, for better logging
lag.log.set_level("DEBUG")

lag.subscribe(GroupMessage, msg_handler)
lag.subscribe(FriendMessage, friend_msg_handler)
lag.subscribe(ServerKick, handle_kick)
lag.subscribe(GroupSign, handle_grp_sign)
lag.subscribe(GroupReaction, handle_group_reaction)
lag.subscribe(GroupAdminChange, handle_group_admin)
# lag.subscribe(FriendRequest, handle_friend_req)


lag.launch()
