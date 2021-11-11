from cesloi.bot_client import Cesloi
from cesloi.event.mirai import NewFriendRequestEvent
from cesloi.model.relation import Friend
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.message.element import Image
from cesloi.message.messageChain import MessageChain
from cesloi.communicate_with_mah import BotSession
from cesloi.alconna import Alconna, Arpamar

sh = SubscriberHandler()
bot = Cesloi(bot_session=BotSession(host="http://localhost:8080", account=1234567890, verify_key="INITKEYWylsVdbr"), debug=True)


@bot.register("FriendMessage")
@sh.set(command=Alconna(headers=["你好", "Hello"], command="World", main_argument=Image))
async def test(app: Cesloi, friend: Friend, message: MessageChain, arpamar: Arpamar):
    print(message.to_text())
    await app.send_with(friend, nudge=True)
    await app.send_friend_message(friend, "Hello,World!")
    if arpamar.matched:
        await app.send_with(friend, MessageChain.create(arpamar.main_argument))


@bot.register("NewFriendRequestEvent")
@sh.set()
async def test1(app: Cesloi, event: NewFriendRequestEvent):
    await event.accept()
    await app.send_friend_message(event.fromId, MessageChain.create([Image.from_local_path("test.png")]))


bot.start()
