from cesloi.bot_client import Cesloi
from cesloi.message.group import Group, Member
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.message.messageChain import MessageChain
from cesloi.communicate_with_mah import BotSession


sh = SubscriberHandler()
bot = Cesloi(bot_session=BotSession(host="http://localhost:8080", account=123456789, verify_key="INITKEYWylsVdbr"))


@bot.register("GroupMessage")
@sh.set(command_headers=['Hello', "你好"])
async def test(app: Cesloi, group: Group, member: Member, message: MessageChain):
    print(message.to_text())
    await app.send_with(member, nudge=True)
    await app.send_group_message(group, "Hello,World!")


@bot.register("MemberLeaveEventKick")
@sh.set()
async def test(app: Cesloi, member: Member = 'target', operator: Member = 'operator'):
    print(member, operator)
    await app.find(operator.id)
    await app.get_profile()
    await app.mute(target=operator)


bot.start()
