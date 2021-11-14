from cesloi.bot_client import Cesloi
from cesloi.event.mirai import NewFriendRequestEvent, MemberLeaveEventKick
from cesloi.event.messages import GroupMessage
from cesloi.model.relation import Friend, Group, Member
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.message.element import Image, Plain
from cesloi.message.messageChain import MessageChain
from cesloi.communicate_with_mah import BotSession
from cesloi.alconna import Alconna, AnyStr, Arpamar, Option
from cesloi.delegatesystem import EventDelegate
from cesloi.timing.schedule import Toconada, Toconado
from cesloi.timing.timers import EveryTimer

ed = EventDelegate()
sh = SubscriberHandler()
bot = Cesloi(
    delegate=ed,
    bot_session=BotSession(
        host="http://localhost:8080",
        account=1234567890,
        verify_key="INITKEYWylsVdbr"
    ),
    debug=False
)
tot = Toconada(ed)

Hello = Alconna(headers=["你好", "Hello"], command=" World", main_argument=Image)
Weather = Alconna(headers=["cmd.", "bot"], command=f"{AnyStr}天气", options=[Option("-d", days=AnyStr)])


@ed.register("FriendMessage")
@sh.set(command=Hello)
async def test(app: Cesloi, friend: Friend, message: MessageChain, arpamar: Arpamar):
    print(message.to_text())
    await app.send_with(friend, nudge=True)
    await app.send_friend_message(friend, "Hello,World!")
    if arpamar.matched:
        await app.send_with(friend, MessageChain.create(arpamar.main_argument))


@ed.register(GroupMessage)
@sh.set(command=Weather,time_schedule=Toconado(EveryTimer().every_minute()))
async def test1(app: Cesloi, city: MessageChain, group: Group, arpamar: Arpamar):
    if arpamar.matched:
        city_name = arpamar.header
        city_day = ""
        if arpamar.has('d'):
            city_day = arpamar.get('d')['days']
        await app.send_group_message(group, MessageChain([Plain(city_name + city_day)]), quote=city.find("Source"))


@ed.register(MemberLeaveEventKick)
@sh.set()
async def test2(app: Cesloi, group: Group, target_member: Member = 'target', operator_member: Member = 'operator'):
    await app.send_with(group, f"{target_member.name} is kicked by {operator_member.name} !")


@ed.register("NewFriendRequestEvent")
@sh.set()
async def test2(app: Cesloi, event: NewFriendRequestEvent):
    await event.accept()
    await app.send_friend_message(event.fromId, MessageChain.create([Image.from_local_path("test.png")]))


@tot.timing(EveryTimer().every_custom_seconds(5))
async def test2():
    await bot.send_friend_message(9876543210, "5s!")



bot.start()
