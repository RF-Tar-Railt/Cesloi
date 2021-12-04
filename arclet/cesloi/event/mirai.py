from datetime import datetime
from typing import Optional, Literal

from pydantic import Field

from .base import MiraiEvent
from ..model.relation import Member, Group, Permission, Friend, Client
from .inserter import ApplicationInserter, EventInserter
from ..utils import bot_application, Structured
from ..message.messageChain import MessageChain


class BotEvent(MiraiEvent):
    """
    指示有关 Bot 本身的事件.
    """


class FriendEvent(MiraiEvent):
    """
    指示有关好友的事件.
    """


class GroupEvent(MiraiEvent):
    """
    指示有关群组的事件.
    """


class BotOnlineEvent(BotEvent):
    """
    Bot登录成功

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
    """

    type = "BotOnlineEvent"
    qq: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter
        )


class BotOfflineEventActive(BotEvent):
    """Bot主动离线

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
    """

    type = "BotOfflineEventActive"
    qq: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter
        )


class BotOfflineEventForce(BotEvent):
    """Bot被挤下线

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
    """

    type = "BotOfflineEventForce"
    qq: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter
        )


class BotOfflineEventDropped(BotEvent):
    """Bot被服务器断开或因网络问题而掉线

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
    """

    type = "BotOfflineEventDropped"
    qq: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter
        )


class BotReloginEvent(BotEvent):
    """Bot主动重新登录

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
    """

    type = "BotReloginEvent"
    qq: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter
        )


class FriendInputStatusChangedEvent(FriendEvent):
    """好友输入状态改变;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Friend (annotation): 发生该事件的好友
    """
    type = "FriendInputStatusChangedEvent"
    friend: Friend
    inputting: bool

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Friend=self.friend
        )


class FriendNickChangedEvent(FriendEvent):
    """好友昵称改变;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Friend (annotation): 发生该事件的好友
    """
    type = "FriendNickChangedEvent"
    friend: Friend
    name_from: str = Field(..., alias="from")
    name_to: str = Field(..., alias="to")

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Friend=self.friend
        )


class BotGroupPermissionChangeEvent(GroupEvent):
    """Bot在群里的权限被改变. 操作人一定是群主;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
    """

    type = "BotGroupPermissionChangeEvent"
    origin: Permission
    current: Permission
    group: Group

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Group=self.group
        )


class BotMuteEvent(GroupEvent):
    """Bot被禁言;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Member (annotation): 执行禁言操作的管理员/群主
        Group (annotation): 发生该事件的群组
    """

    type = "BotMuteEvent"
    durationSeconds: int
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.operator.group
        )


class BotUnmuteEvent(GroupEvent):
    """Bot被取消禁言;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Member (annotation): 执行解除禁言操作的管理员/群主, 若为 None 则为应用实例所辖账号操作
        Group (annotation): 发生该事件的群组
    """

    type = "BotUnmuteEvent"
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.operator.group
        )


class BotJoinGroupEvent(GroupEvent):
    """Bot加入了一个新群

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Group (annotation): 发生该事件的群组
    """

    type = "BotJoinGroupEvent"
    group: Group

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            Group=self.group
        )


class BotLeaveEventActive(GroupEvent):
    """Bot主动退出一个群

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Group (annotation): 发生该事件的群组
    """

    type: str = "BotLeaveEventActive"
    group: Group

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            Group=self.group
        )


class BotLeaveEventKick(GroupEvent):
    """Bot被踢出一个群

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Member (annotation): 执行本操作的群成员
        Group (annotation): 发生该事件的群组
    """

    type: str = "BotLeaveEventKick"
    group: Group
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Group=self.group,
            Member=self.operator
        )


class GroupRecallEvent(GroupEvent):
    """群消息被撤回;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Member (annotation): 执行本操作的群成员
        Group (annotation): 发生该事件的群组
    """

    type = "GroupRecallEvent"
    authorId: int
    messageId: int
    time: datetime
    group: Group
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.group
        )


class FriendRecallEvent(FriendEvent):
    """好友消息被撤回;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
    """

    type = "FriendRecallEvent"
    authorId: int
    messageId: int
    time: int
    operator: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter
        )


class NudgeSubject(Structured):
    id: int
    kind: str


class NudgeEvent(GroupEvent):
    """戳一戳事件;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
    """

    type: str = "NudgeEvent"
    fromId: int
    action: str
    suffix: str
    target: int
    subject: NudgeSubject

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter
        )


class GroupNameChangeEvent(GroupEvent):
    """某个群名被改变;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 被修改了群名称的群组
        Member (annotation): 更改群名称的成员, 权限必定为管理员或是群主
    """

    type = "GroupNameChangeEvent"
    origin: str
    current: str
    group: Group
    operator: Optional[Member] = None

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.group
        )


class GroupEntranceAnnouncementChangeEvent(GroupEvent):
    """某群入群公告被改变;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 被修改了入群公告的群组
        Member (annotation): 作出此操作的管理员/群主
    """

    type = "GroupEntranceAnnouncementChangeEvent"
    origin: str
    current: str
    group: Group
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.group
        )


class GroupMuteAllEvent(GroupEvent):
    """有一群组开启/关闭了全体禁言;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 全体禁言状态改变的群组
        Member (annotation): 作出此操作的管理员/群主
    """

    type = "GroupMuteAllEvent"
    origin: bool
    current: bool
    group: Group
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.group
        )


class GroupAllowAnonymousChatEvent(GroupEvent):
    """有一群组开启/关闭了匿名聊天;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 修改了相关设定的群组
        Member (annotation): 作出此操作的管理员/群主
    """

    type = "GroupAllowAnonymousChatEvent"
    origin: bool
    current: bool
    group: Group
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.group
        )


class GroupAllowConfessTalkEvent(GroupEvent):
    """有一群组开启/关闭了坦白说;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 修改了相关设定的群组
    """

    type = "GroupAllowAnonymousChatEvent"
    origin: bool
    current: bool
    group: Group
    isByBot: bool

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Group=self.group
        )


class GroupAllowMemberInviteEvent(GroupEvent):
    """有一群组修改了该群是否允许群员邀请其他用户加入群组的功能;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 修改了该功能的群组
        Member (annotation): 作出此操作的管理员/群主
    """

    type = "GroupAllowMemberInviteEvent"
    origin: bool
    current: bool
    group: Group
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.operator,
            Group=self.group
        )


class MemberJoinEvent(GroupEvent):
    """新人入群的事件

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Group (annotation): 该用户加入的群组
        Member (annotation): 该用户的信息
    """

    type = "MemberJoinEvent"
    member: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            Member=self.member,
            Group=self.member.group
        )


class MemberLeaveEventKick(GroupEvent):
    """成员被踢出群（该成员不是Bot）;当 `operator` 为 `None` 时, 执行者为Bot

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Group (annotation): 指定的群组
        Member (annotation):
          - `"target"` (default, const, str): 被踢者的信息
          - `"operator"` (default, const, str): 执行了该操作的管理员/群主, 也可能是Bot.
    """

    type = "MemberLeaveEventKick"
    member: Member
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            Group=self.member.group,
            target=self.member,
            operator=self.operator
        )


class MemberLeaveEventQuit(GroupEvent):
    """成员主动离群（该成员不是Bot）

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Group (annotation): 发生本事件的群组, 通常的, 在本事件发生后本群组成员数量少于之前
        Member (annotation): 退群群员的信息
    """

    type = "MemberLeaveEventQuit"
    member: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            Member=self.member,
            Group=self.member.group
        )


class MemberCardChangeEvent(GroupEvent):
    """群名片改动;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
        Member (annotation): 名片改动的群员的信息
    """

    type = "MemberCardChangeEvent"
    origin: str
    current: str
    member: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.member,
            Group=self.member.group
        )


class MemberSpecialTitleChangeEvent(GroupEvent):
    """群头衔改动（只有群主有操作限权）;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
        Member (annotation): 被更改群头衔的群组成员
    """

    type = "MemberSpecialTitleChangeEvent"
    origin: str
    current: str
    member: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.member,
            Group=self.member.group
        )


class MemberPermissionChangeEvent(GroupEvent):
    """成员权限改变的事件（该成员不是Bot）;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
        Member (annotation): 被调整权限的群组成员
    """

    type = "MemberPermissionChangeEvent"
    origin: str
    current: str
    member: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.member,
            Group=self.member.group
        )


class MemberMuteEvent(GroupEvent):
    """群成员被禁言事件（该成员不是Bot）;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
        Member (annotation):
          - `"target"` (default, const, str): 被禁言的群员的信息
          - `"operator"` (default, const, str): 操作者的信息，当None时为Bot操作
    """

    type = "MemberMuteEvent"
    durationSeconds: int
    member: Member
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Group=self.member.group,
            target=self.member,
            operator=self.operator
        )


class MemberUnmuteEvent(GroupEvent):
    """群成员被取消禁言事件（该成员不是Bot）;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
        Member (annotation):
          - `"target"` (default, const, str): 被禁言的群员的信息
          - `"operator"` (default, const, str): 操作者的信息，当None时为Bot操作
    """

    type = "MemberUnmuteEvent"
    member: Member
    operator: Optional[Member]

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Group=self.member.group,
            target=self.member,
            operator=self.operator
        )


class MemberHonorChangeEvent(GroupEvent):
    """群员称号改变;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Group (annotation): 发生该事件的群组
        Member (annotation): 称号改变的群组成员
    """
    type = "MemberHonorChangeEvent"
    action: str
    honor: Literal["achieve", "lose"]
    member: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Member=self.member,
            Group=self.member.group
        )


class RequestEvent(MiraiEvent):
    type: str
    eventId: int
    fromId: int
    groupId: Optional[int]
    nick: str
    message: Optional[str] = ""

    async def response_event(self, operate: int, msg: Optional[str] = ""):
        bot = bot_application.get()
        await bot.communicator.send_handle(
            f"resp/{self.type[0].lower() + self.type[1:]}",
            "POST",
            {
                "sessionKey": bot.bot_session.sessionKey,
                "eventId": self.eventId,
                "fromId": self.fromId,
                "groupId": self.groupId,
                "operate": operate,
                "message": msg
            }
        )


class NewFriendRequestEvent(RequestEvent):
    """添加好友申请;可使用原始事件类作为参数, 以此获得该事件实例, 以获取更多的信息

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例

    参数说明:
        1. event.fromId: int - 申请人QQ号
        2. event.groupId: int - 申请人如果通过某个群添加好友，该项为该群群号；否则为0
        3. event.nick: str  - 申请人的昵称或群名片
        4. event.message: str  - 申请消息
    方法说明:
        1. 同意添加好友: await event.accept()
        2. 拒绝添加好友: await event.reject()
        3. 拒绝并不再接收该用户的好友申请: await event.block()
    """
    type = "NewFriendRequestEvent"

    async def accept(self, message: str = ""):
        await self.response_event(0, message)

    async def reject(self, message: str = ""):
        await self.response_event(1, message)

    async def block(self, message: str = ""):
        await self.response_event(2, message)

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter
        )


class MemberJoinRequestEvent(RequestEvent):
    """用户入群申请;该事件需要你将事件实例作为参数，以进行操作

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例

    参数说明:
        1. event.fromId: int - 申请人QQ号
        2. event.groupId: int - 申请人申请入群的群号
        3. event.groupName: str - 申请人申请入群的群名称
        4. event.nick: str  - 申请人的昵称或群名片
        5. event.message: str  - 申请消息
    方法说明:
        1. 同意入群: await event.accept()
        2. 拒绝入群: await event.reject()
        3. 忽略请求: await event.ignore()
        4. 拒绝并不再接收该用户的入群申请: await event.reject_and_block()
        5. 忽略并不再接收该用户的入群申请: await event.ignore_and_block()
    """
    type = "MemberJoinRequestEvent"
    groupName: str

    async def accept(self, message: str = ""):
        await self.response_event(0, message)

    async def reject(self, message: str = ""):
        await self.response_event(1, message)

    async def ignore(self, message: str = ""):
        await self.response_event(2, message)

    async def reject_and_block(self, message: str = ""):
        await self.response_event(3, message)

    async def ignore_and_block(self, message: str = ""):
        await self.response_event(4, message)

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter
        )


class BotInvitedJoinGroupRequestEvent(RequestEvent):
    """Bot被邀请入群申请;该事件需要你将事件实例作为参数，以进行操作

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例

        Event (annotation): 该事件的实例

    参数说明:
        1. event.fromId: int - 邀请人（好友）的QQ号
        2. event.groupId: int - 被邀请进入群的群号
        3. event.groupName: str - 被邀请进入群的群名称
        4. event.nick: str  - 邀请人（好友）的昵称
        5. event.message: str  - 邀请消息
    方法说明:
        1. 同意邀请: await event.accept()
        2. 拒绝邀请: await event.reject()
    """
    type = "BotInvitedJoinGroupRequestEvent"
    groupName: str

    async def accept(self, message: str = ""):
        await self.response_event(0, message)

    async def reject(self, message: str = ""):
        await self.response_event(1, message)

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter
        )


class OtherClientOnlineEvent(MiraiEvent):
    """其他客户端上线;该事件需要你将事件实例作为参数，以进行操作

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Event (annotation): 该事件的实例
        Client (annotation): 其他客户端的信息
    """
    type = "OtherClientOnlineEvent"
    client: Client
    kind: int

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            Client=self.client
        )


class OtherClientOfflineEvent(MiraiEvent):
    """其他客户端下线

    该事件可提供的参数:
        Cesloi (annotation): 发布事件的应用实例
        Client (annotation): 其他客户端的信息
    """
    type = "OtherClientOfflineEvent"
    client: Client

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            Client=self.client
        )


class CommandExecutedEvent(MiraiEvent):
    type = "CommandExecutedEvent"
    name: str
    args: MessageChain

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.args
        )
