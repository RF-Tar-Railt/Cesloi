import asyncio
from arclet.cesloi.bot_client import Cesloi
from arclet.cesloi.event.mirai import NewFriendRequestEvent, MemberLeaveEventKick
from arclet.cesloi.event.messages import GroupMessage
from arclet.cesloi.model.relation import Friend, Group, Member
from arclet.cesloi.message.element import Image, Plain
from arclet.cesloi.message.messageChain import MessageChain
from arclet.cesloi.communicate_with_mah import BotSession
from arclet.cesloi.message.alconna import Alconna, AnyStr, Arpamar, Option, AlconnaParser
from arclet.cesloi.timing.schedule import Toconada
from arclet.cesloi.timing.timers import EveryTimer
from arclet.letoderea import EventSystem

loop = asyncio.new_event_loop()
es = EventSystem(loop=loop)
bot = Cesloi(
    event_system=es,
    bot_session=BotSession(
        host="http://localhost:8080",
        account=1234567890,
        verify_key="INITKEYWylsVdbr"
    ),
    debug=False
)
tot = Toconada(es)

Hello = Alconna(headers=["你好", "Hello"], command=" World", main_argument=Image)
Weather = Alconna(headers=["cmd.", "bot"], command=f"{AnyStr}天气", options=[Option("-d", days=AnyStr)])


@es.register("FriendMessage", decorators=[AlconnaParser(alconna=Hello)])
async def test(app: Cesloi, friend: Friend, message: MessageChain, arpamar: Arpamar):
    print(message.to_text())
    await app.send_with(friend, nudge=True)
    await app.send_friend_message(friend, "Hello,World!")
    if arpamar.matched:
        await app.send_with(friend, MessageChain.create(arpamar.main_argument))


@es.register(GroupMessage, decorators=[AlconnaParser(alconna=Weather)])
async def test1(app: Cesloi, city: MessageChain, group: Group, arpamar: Arpamar):
    if arpamar.matched:
        city_name = arpamar.header
        city_day = ""
        if arpamar.has('d'):
            city_day = arpamar.get('d')['days']
        await app.send_group_message(group, MessageChain([Plain(city_name + city_day)]), quote=city.find("Source"))


@es.register(MemberLeaveEventKick)
async def test2(app: Cesloi, group: Group, target_member: Member = 'target', operator_member: Member = 'operator'):
    await app.send_with(group, f"{target_member.name} is kicked by {operator_member.name} !")


@es.register("NewFriendRequestEvent")
async def test2(app: Cesloi, event: NewFriendRequestEvent):
    await event.accept()
    await app.send_friend_message(event.fromId, MessageChain.create([Image(path="test.png")]))


@tot.timing(EveryTimer().every_custom_seconds(5))
async def test2():
    await bot.send_friend_message(9876543210, "5s!")


bot.start()
