from cesloi.bot_client import Cesloi
from cesloi.event.mirai import NewFriendRequestEvent
from cesloi.model.relation import Friend
from cesloi.message.element import Image
from cesloi.message.messageChain import MessageChain
from cesloi.alconna import Alconna, Arpamar
from cesloi.plugin import Bellidin as bd


@bd.model_register(
    "FriendMessage",
    match_command=Alconna(headers=["你好", "Hello"], command=" World", main_argument=Image)
)
async def test(app: Cesloi, friend: Friend, message: MessageChain, arpamar: Arpamar):
    print(message.to_text())
    await app.send_with(friend, nudge=True)
    await app.send_friend_message(friend, "Hello,World!")
    if arpamar.matched:
        await app.send_with(friend, MessageChain.create(arpamar.main_argument))


@bd.model_register("NewFriendRequestEvent")
async def test1(app: Cesloi, event: NewFriendRequestEvent):
    await event.accept()
    await app.send_friend_message(event.fromId, MessageChain.create([Image.from_local_path("test.png")]))
