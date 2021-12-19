from arclet.cesloi.bot_client import Cesloi
from arclet.cesloi.event.mirai import NewFriendRequestEvent
from arclet.cesloi.model.relation import Friend
from arclet.cesloi.message.element import Image
from arclet.cesloi.message.messageChain import MessageChain
from arclet.cesloi.communicate_with_mah import BotSession
from arclet.cesloi.message.alconna import Alconna, Arpamar, AlconnaParser
from arclet.cesloi.timing.schedule import Toconada, Toconado
from arclet.cesloi.timing.timers import EveryTimer

bot = Cesloi(bot_session=BotSession(host="http://localhost:8080", account=1234567890, verify_key="INITKEYWylsVdbr"),
             debug=True)
tot = Toconada(bot.event_system)


@bot.register(
    "FriendMessage",
    conditions=[Toconado(EveryTimer().every_second())],
    decorators=[AlconnaParser(alconna=Alconna(headers=["你好", "Hello"], command="World", main_argument=Image))]
)
async def test(app: Cesloi, friend: Friend, message: MessageChain, arpamar: Arpamar):
    print(message.to_text())
    await app.send_with(friend, "Hello,World!", nudge=True)
    if arpamar.matched:
        await app.send_with(friend, MessageChain.create(arpamar.main_args))

@bot.register("NewFriendRequestEvent")
async def test1(app: Cesloi, event: NewFriendRequestEvent):
    await event.accept()
    await app.send_friend_message(event.fromId, MessageChain.create([Image(path="test.png")]))


@tot.timing(EveryTimer().every_custom_seconds(50))
async def test2():
    await bot.send_friend_message(3165388245, "50s!")


bot.start()
