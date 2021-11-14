from cesloi.bot_client import Cesloi
from cesloi.event.mirai import NewFriendRequestEvent
from cesloi.model.relation import Friend
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.message.element import Image
from cesloi.message.messageChain import MessageChain
from cesloi.communicate_with_mah import BotSession
from cesloi.alconna import Alconna, Arpamar
from cesloi.timing.schedule import Toconada, Toconado
from cesloi.timing.timers import EveryTimer

sh = SubscriberHandler()
bot = Cesloi(bot_session=BotSession(host="http://localhost:8080", account=123456789, verify_key="INITKEYWylsVdbr"), debug=False)
tot = Toconada(bot.delegate)


@bot.register("FriendMessage")
@sh.set(command=Alconna(headers=["你好", "Hello"], command="World", main_argument=Image), time_schedule=Toconado(EveryTimer().every_minute()))
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


@tot.timing(EveryTimer().every_custom_seconds(5))
async def test2():
    await bot.send_friend_message(9876543210, "5s!")

bot.start()
