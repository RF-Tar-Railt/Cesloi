"""
该文件为Cesloi的小型集成库
"""
from .bot_client import Cesloi
from .model.relation import Group, Member, Friend
from ..letoderea.entities.subscriber import Subscriber
from .communicate_with_mah import BotSession
from .message.messageChain import MessageChain
from .event.messages import GroupMessage, FriendMessage, TempMessage


class CesloiMini:
    """
    Cesloi的小型集成库,只选择了基础功能
    """
    def __init__(self, host, qq, verify_key):
        self.client = Cesloi
        self.app = Cesloi(
            bot_session=BotSession(host=host, account=qq, verify_key=verify_key),
            debug=True)
        self.Friend = Friend
        self.Group = Group
        self.Member = Member
        self.Message = MessageChain
        self.GroupMessage = GroupMessage
        self.FriendMessage = FriendMessage
        self.TempMessage = TempMessage

    def register(self, *args, **kwargs):
        """
        注册事件方法，用于指定订阅器订阅的发布器绑定的事件。
        """
        def _wrapper(func):
            return self.app.register(*args, **kwargs)(Subscriber.set()(func))
        return _wrapper

    def run(self):
        return self.app.start()
