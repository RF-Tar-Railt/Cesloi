from cesloi.bot_client import Cesloi
from cesloi.event.mirai import NewFriendRequestEvent, MemberLeaveEventKick
from cesloi.event.messages import GroupMessage
from cesloi.model.relation import Friend, Group, Member
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.message.element import Image, Plain
from cesloi.message.messageChain import MessageChain
from cesloi.communicate_with_mah import BotSession
from cesloi.command import Command, AnyStr
from cesloi.delegatesystem import EventDelegate

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


@ed.register("FriendMessage")
@sh.set(command=Command(headers=["你好", "Hello"], main=["World"]))
async def test(app: Cesloi, friend: Friend, message: MessageChain):
    print(message.to_text())
    await app.send_with(friend, nudge=True)
    await app.send_friend_message(friend, "Hello,World!")
    await app.send_with(friend, MessageChain([message.find(Image)]))


@ed.register(GroupMessage)
@sh.set(command=Command(["cmd.", "bot"], [f"{AnyStr}天气", ["=", AnyStr, ""], ""]),
        require_param_name="city",
        is_replace_message=True)
async def test1(app: Cesloi, city: MessageChain, group: Group):
    city_list = city.to_text().split(',')
    city_name = city_list[0]
    await app.send_group_message(group, MessageChain([Plain(city_name)]), quote=city.find("Source"))


@ed.register(MemberLeaveEventKick)
@sh.set()
async def test2(app: Cesloi, group: Group, target_member: Member = 'target', operator_member: Member = 'operator'):
    await app.send_with(group, f"{target_member.name} is kicked by {operator_member.name} !")


@ed.register("NewFriendRequestEvent")
@sh.set()
async def test2(app: Cesloi, event: NewFriendRequestEvent):
    await event.accept()
    await app.send_friend_message(event.fromId, MessageChain.create([Image.from_local_path("test.png")]))


bot.start()
