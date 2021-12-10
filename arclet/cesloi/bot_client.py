import asyncio
import sys
import time
import traceback
from asyncio import Task
from typing import Optional, Union, List, Type

from arclet.cesloi.utils import enter_message_send_context, UploadMethods, bot_application_context_manager, \
    upload_method
from arclet.letoderea import EventSystem, Condition_T, TemplateDecorator, TemplateEvent
from arclet.cesloi.event.lifecycle import ApplicationRunning, ApplicationStop
from arclet.cesloi.event.messages import Message, GroupMessage, FriendMessage, TempMessage
from arclet.cesloi.logger import Logger
from arclet.cesloi.communicate_with_mah import BotSession, Communicator
from arclet.cesloi.model.utils import BotMessage, Profile, FileInfo
from arclet.cesloi.message.element import Source, MessageElement
from arclet.cesloi.model.relation import Group, Member, GroupConfig, MemberInfo, Friend
from arclet.cesloi.message.messageChain import MessageChain
from arclet.cesloi.plugin import Bellidin


class Cesloi:
    def __init__(
            self,
            *,
            bot_session: BotSession,
            event_system: Optional[EventSystem] = None,
            logger: Optional[Logger] = None,
            debug: bool = False,
            enable_chat_log: bool = True,
            use_loguru_traceback: Optional[bool] = True,
    ):
        self.event_system: EventSystem = event_system or EventSystem()
        self.bot_session: BotSession = bot_session
        self.debug = debug
        self.logger = logger or Logger(level='DEBUG' if debug else 'INFO').logger
        self.bellidin = Bellidin.set_bellidin(self.event_system, self.logger)
        self.chat_log_enabled = enable_chat_log
        self.communicator = Communicator(bot_session, bot=self, event_system=self.event_system, logger=self.logger)
        self.running: bool = False
        self.daemon_task: Optional[Task] = None
        self.group_message_log_format: str = "{bot_id}: [{group_name}({group_id})] {member_name}({member_id}) -> {" \
                                             "message_string} "
        self.friend_message_log_format: str = "{bot_id}: [{friend_name}({friend_id})] -> {message_string}"
        self.temp_message_log_format: str = "{bot_id}: [{group_name}({group_id}.{member_name}({member_id})] -> {" \
                                            "message_string} "

        if self.chat_log_enabled:
            self.event_system.register("GroupMessage")(self.logger_group_message)
            self.event_system.register("FriendMessage")(self.logger_friend_message)
            self.event_system.register("TempMessage")(self.logger_temp_message)

        if use_loguru_traceback:
            traceback.print_exception = self.loguru_excepthook
            sys.excepthook = self.loguru_excepthook
            self.event_system.loop.set_exception_handler(self.loguru_async_handler)

    @staticmethod
    def loguru_excepthook(cls, val, tb, *_, **__):
        Logger.logger.opt(exception=(cls, val, tb)).error(f"Exception:")

    @staticmethod
    def loguru_async_handler(loop, ctx: dict):
        Logger.logger.opt(exception=(Exception, ctx["message"], ctx["source_traceback"])).error(
            f"Exception:"
        )

    async def logger_group_message(self, event: GroupMessage):
        self.logger.info(
            self.group_message_log_format.format_map(
                dict(
                    group_id=event.sender.group.id,
                    group_name=event.sender.group.name,
                    member_id=event.sender.id,
                    member_name=event.sender.name,
                    bot_id=self.bot_session.account,
                    message_string=event.messageChain.__repr__(),
                )
            )
        )

    async def logger_friend_message(self, event: FriendMessage):
        self.logger.info(
            self.friend_message_log_format.format_map(
                dict(
                    bot_id=self.bot_session.account,
                    friend_name=event.sender.nickname,
                    friend_id=event.sender.id,
                    message_string=event.messageChain.__repr__(),
                )
            )
        )

    async def logger_temp_message(self, event: TempMessage):
        self.logger.info(
            self.temp_message_log_format.format_map(
                dict(
                    group_id=event.sender.group.id,
                    group_name=event.sender.group.name,
                    member_id=event.sender.id,
                    member_name=event.sender.name,
                    bot_id=self.bot_session.account,
                    message_string=event.messageChain.__repr__(),
                )
            )
        )

    async def running_task(self, retry_interval: float = 5.0):
        self.logger.debug("Cesloi Network Started.")
        while self.running:
            try:
                await self.communicator.connect()
                try:
                    if self.communicator.running_task:
                        await self.communicator.running_task
                except Exception as e:
                    self.logger.warning(e)
                await self.communicator.stop()
                self.logger.warning("Communicator stopped")
                await asyncio.sleep(retry_interval)
                self.logger.info("Cesloi Network Restarting...")
            except asyncio.CancelledError:
                await self.communicator.stop()
        self.logger.debug("Cesloi Network Stopped.")

    async def close(self):
        if self.running:
            self.event_system.event_spread(ApplicationStop(self))
            self.running = False
            self.uninstall_plugins()
            if self.daemon_task:
                self.daemon_task.cancel()
                self.daemon_task = None
            await self.communicator.stop()
            for t in asyncio.all_tasks(self.event_system.loop):
                if (
                        t is not asyncio.current_task(self.event_system.loop)
                        and not t.get_name().startswith("cesloi")
                        and not t.get_name().startswith("_")
                ):
                    t.cancel()
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        if self.event_system:
            loop = self.event_system.loop
        else:
            loop = loop or asyncio.get_event_loop()

        try:
            if not self.running:
                self.running = True
                start_time = time.time()
                self.logger.info("Cesloi Application Starting...")
                self.daemon_task = loop.create_task(self.running_task(), name="cesloi_web_task")
                while not self.bot_session.sessionKey:
                    loop.run_until_complete(asyncio.sleep(0.001))
                self.event_system.event_spread(ApplicationRunning(self))
                self.logger.info(f"Cesloi Application Started with {time.time() - start_time:.2}s")

            if self.daemon_task:
                loop.run_until_complete(self.daemon_task)
        except KeyboardInterrupt or asyncio.CancelledError:
            self.logger.warning("Interrupt detected, bot stopping ...")
        loop.run_until_complete(self.close())
        self.logger.info("Cesloi shutdown. Have a nice day!")

    def register(
            self, event: Union[str, Type[TemplateEvent]],
            *,
            priority: int = 16,
            conditions: List[Condition_T] = None,
            decorators: List[TemplateDecorator] = None
    ):
        """
        注册事件方法，用于指定订阅器订阅的发布器绑定的事件。
        """
        return self.event_system.register(event, priority=priority, conditions=conditions, decorators=decorators)

    def install_plugins(self, plugins_dir: str):
        """
        导入插件方法，必须传入一个目录，目录内有你的.py文件或模块
        """
        return self.bellidin.install_plugins(plugins_dir)

    def uninstall_plugins(self):
        """
        卸载导入的插件的方法.
        """
        return self.bellidin.uninstall_plugins()

    def reload_plugins(self, new_plugins_dir: Optional[str] = None):
        """
        重载插件方法，可选传入一个新目录，目录内有你的.py文件或模块
        """
        return self.bellidin.reload_plugins(new_plugins_dir)

    async def get_mah_version(self):
        result = await self.communicator.send_handle("about", "GET")
        return result['version']

    async def get_from_messageId(self, messageId: int):
        result = await self.communicator.send_handle(
            "messageFromId",
            "GET",
            {"sessionKey": self.bot_session.sessionKey, "id": messageId}
        )
        return MessageChain.parse_obj(result['messageChain'])

    async def get_friend_list(self):
        result = await self.communicator.send_handle(
            "friendList",
            "GET",
            {"sessionKey": self.bot_session.sessionKey}
        )
        return [Friend.parse_obj(i) for i in result]

    async def get_group_list(self):
        result = await self.communicator.send_handle(
            "groupList",
            "GET",
            {"sessionKey": self.bot_session.sessionKey}
        )
        return [Group.parse_obj(i) for i in result]

    async def get_member_list(self, group: Union[Group, int]):
        result = await self.communicator.send_handle(
            "memberList",
            "GET",
            {"sessionKey": self.bot_session.sessionKey,
             "target": group if isinstance(group, int) else group.id}
        )
        return [Member.parse_obj(i) for i in result]

    async def find(
            self,
            target_id: Optional[int] = None,
            group: Optional[Union[Group, int]] = None
    ) -> Optional[Union[Friend, Group, Member]]:
        """根据提供的参数自动尝试从好友列表、群列表或群成员列表中获取目标信息；可能返回None

        只填target则尝试在好友列表中搜索；只填group则尝试在群列表中搜索；两者都填则尝试在指定群组中搜索成员

        Args:
            target_id : 已知的好友id或者群成员id
            group : 尝试获取的已知的群组
        """
        if target_id and not group:
            data_friend = await self.get_friend_list()
            for i in data_friend:
                if i.id == target_id:
                    return i
        if group and not target_id:
            if isinstance(group, Group):
                group = group.id
            data_group = await self.get_group_list()
            for i in data_group:
                if i.id == group:
                    return i
        if group and target_id:
            data_member = await self.get_member_list(group)
            for i in data_member:
                if i.id == target_id:
                    return i

    async def get_bot_profile(self):
        result = await self.communicator.send_handle(
            "botProfile",
            "GET",
            {"sessionKey": self.bot_session.sessionKey}
        )
        return Profile.parse_obj(result)

    async def get_friend_profile(self, target: Union[Friend, int]):
        result = await self.communicator.send_handle(
            "friendProfile",
            "GET",
            {"sessionKey": self.bot_session.sessionKey,
             "target": target if isinstance(target, int) else target.id}
        )
        return Profile.parse_obj(result)

    async def get_member_profile(self, target: Union[Member, int], group: Optional[Union[Group, int]] = None):
        group = group or (target.group if isinstance(target, Member) else None)
        if not group:
            raise ValueError("Missing argument: group")
        result = await self.communicator.send_handle(
            "memberProfile",
            "GET",
            {"sessionKey": self.bot_session.sessionKey,
             "target": group if isinstance(group, int) else group.id,
             "memberId": target if isinstance(target, int) else target.id
             }
        )
        return Profile.parse_obj(result)

    async def get_profile(self, target: Optional[Union[Member, Friend, int]] = None,
                          group: Optional[Union[Group, int]] = None):
        """根据提供的参数自动尝试获取对象的资料

        若不填参数，则考虑获取机器人自身资料；若只填入target并且填入的为数字，则优先考虑获取好友资料；若填入group，则target为必填

        Args:
            target : 已知的好友或者群成员
            group : 已知的群组
        """
        if target and group:
            if isinstance(target, Member) or isinstance(target, int):
                return await self.get_member_profile(target, group)
            return await self.get_friend_profile(target)
        if target and not group:
            if isinstance(target, Friend) or isinstance(target, int):
                return await self.get_friend_profile(target)
            return await self.get_member_profile(target)
        if not target and group:
            raise ValueError("Missing argument: target")
        return await self.get_bot_profile()

    @bot_application_context_manager
    async def send_friend_message(
            self,
            target: Union[Friend, int],
            message: Union[MessageChain, str],
            *,
            quote: Optional[Union[Source, int]] = None,
    ) -> BotMessage:
        """使用此方法向指定好友发送消息, 可以指定需要回复的消息.

        Args:
            target : 指定的好友
            message : 消息链
            quote : 需要回复的消息源, 默认为 None.

        Returns:
            BotMessage:含有一 `messageId` 属性, 可用于回复.
        """
        if isinstance(message, str):
            message = MessageChain.create(message)
        with enter_message_send_context(UploadMethods.Friend):
            target_id = target.id if isinstance(target, Friend) else target
            result = await self.communicator.send_handle(
                "sendFriendMessage",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "target": target_id,
                    "messageChain": message.dict()["__root__"],
                    **(
                        {"quote": quote.id if isinstance(quote, Source) else quote} if quote else {}
                    )
                }
            )
            self.logger.info(f"[BOT {self.bot_session.account}] Friend({target_id}) <- {message.to_text()}")
            return BotMessage.parse_obj({"messageId": result['messageId']})

    @bot_application_context_manager
    async def send_group_message(
            self,
            target: Union[Group, int],
            message: Union[MessageChain, str],
            *,
            quote: Optional[Union[Source, int]] = None,
    ) -> BotMessage:
        """使用此方法向指定群组发送消息, 可以指定需要回复的消息.

        Args:
            target : 指定的群组.
            message : 消息链
            quote : 需要回复的消息源, 默认为 None.

        Returns:
            BotMessage:含有一 `messageId` 属性, 可用于回复.
        """
        if isinstance(message, str):
            message = MessageChain.create(message)
        with enter_message_send_context(UploadMethods.Group):
            target_id = target.id if isinstance(target, Group) else target
            result = await self.communicator.send_handle(
                "sendGroupMessage",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "target": target_id,
                    "messageChain": message.dict()["__root__"],
                    **(
                        {"quote": quote.id if isinstance(quote, Source) else quote} if quote else {}
                    )
                }
            )
            self.logger.info(f"[BOT {self.bot_session.account}] Group({target_id}) <- {message.to_text()}")
            return BotMessage.parse_obj({"messageId": result['messageId']})

    @bot_application_context_manager
    async def send_temp_message(
            self,
            target: Union[Member, int],
            message: Union[MessageChain, str],
            group: Optional[Union[Group, int]] = None,
            *,
            quote: Optional[Union[Source, int]] = None,
    ) -> BotMessage:
        """使用此方法向指定群组中的特定组员发送消息, 可指定需要回复的消息.

        Args:
            target : 指定的群组成员.
            group : 指定的群组.
            message : 消息链.
            quote : 需要回复的消息源, 默认为 None.

        Returns:
            BotMessage:含有一 `messageId` 属性, 可用于回复.
        """
        if isinstance(message, str):
            message = MessageChain.create(message)
        group = target.group if (isinstance(target, Member) and not group) else group
        if not group:
            raise ValueError("Missing argument: group")
        with enter_message_send_context(UploadMethods.Temp):
            group_id = group.id if isinstance(group, Group) else group
            target_id = target.id if isinstance(target, Member) else target
            result = await self.communicator.send_handle(
                "sendTempMessage",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "group": group_id,
                    "qq": target_id,
                    "messageChain": message.dict()["__root__"],
                    **(
                        {"quote": quote.id if isinstance(quote, Source) else quote} if quote else {}
                    )
                }
            )
            self.logger.info(
                f"[BOT {self.bot_session.account}] Member({target_id}, in {group_id}) <- {message.to_text()}")
            return BotMessage.parse_obj({"messageId": result['messageId']})

    @bot_application_context_manager
    async def send_with(
            self,
            target: Union[Friend, Group, Member, Message],
            messages: Optional[Union[MessageChain, str, List[MessageElement], MessageElement]] = None,
            *,
            quote: Optional[Union[Source, int]] = None,
            nudge: bool = False
    ):
        """应用发送消息操作的统合方法

        Args:
            target : 指定的好友、群组、群组成员、甚至是事件实例
            messages : 消息链
            quote : 需要回复的消息源, 默认为 None.
            nudge : 是否发送戳一戳，默认为False.

        Returns:
            BotMessage:含有一 `messageId` 属性, 可用于回复.

        """
        if isinstance(target, (GroupMessage, FriendMessage, TempMessage)):
            target = target.sender
        else:
            target = target
        if nudge:
            if isinstance(target, Friend) or isinstance(target, Member):
                await self.send_nudge(target)
        if messages:
            data = {"message": messages, "target": target}
            if quote:
                data["quote"] = quote
            if isinstance(target, Friend):
                return await self.send_friend_message(**data)
            elif isinstance(target, Group):
                return await self.send_group_message(**data)
            elif isinstance(target, Member):
                return await self.send_temp_message(**data)
            else:
                raise ValueError(
                    f"target {target} unclear! Please take an instance of the dialog object type as a parameter"
                )

    async def send_nudge(self, target: Union[Friend, Member, int]):
        target_id = target if isinstance(target, int) else target.id
        await self.communicator.send_handle(
            "sendNudge",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": target_id,
                "subject": target.group.id if isinstance(target, Member) else target_id,
                "kind": "Group" if isinstance(target, Member) else "Friend"
            }
        )
        self.logger.info(
            f"[BOT {self.bot_session.account}] Member({target_id}) <- Nudge")

    async def recall_message(self, target: Union[Source, BotMessage, int]):
        """
        使用此方法撤回一指定消息
        """
        if isinstance(target, Source):
            target = target.id
        if isinstance(target, BotMessage):
            target = target.messageId

        await self.communicator.send_handle(
            "recall",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": target,
            }
        )

    async def delete_friend(self, target: Union[Friend, int]):
        """
        使用此方法删除指定好友
        """
        friend_id = target.id if isinstance(target, Friend) else target
        await self.communicator.send_handle(
            "deletaFriend",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": friend_id,
            }
        )

    async def mute(
            self,
            target: Optional[Union[Member, int]] = None,
            group: Optional[Union[Group, int]] = None,
            mute_time: int = 60, mute_all: bool = False
    ):
        """
        使用此方法指定群禁言指定群员或开启全体禁言（需要有相关限权）

        Args:
            target : 指定成员.
            group : 指定群组.
            mute_time : 禁言时长，单位为秒，最多30天，默认为60秒.
            mute_all : 是否开启全体禁言,要求群组参数为必填.
        """
        if target:
            if not group:
                if isinstance(target, Member):
                    group_id = target.group.id
                else:
                    raise ValueError("Missing Argument: group")
            else:
                group_id = group.id if isinstance(group, Group) else group
            await self.communicator.send_handle(
                "mute",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "target": group_id,
                    "memberId": target.id if isinstance(target, Member) else target,
                    "time": mute_time
                }
            )
        elif group and mute_all:
            await self.communicator.send_handle(
                "muteAll",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "target": group.id if isinstance(group, Group) else group
                }
            )

    async def unmute(self, target: Optional[Union[Member, int]] = None, group: Optional[Union[Group, int]] = None,
                     unmute_all: bool = False):
        """
        使用此方法指定群解除群成员禁言或解除全体禁言（需要有相关限权）

        Args:
            target : 指定成员;
            group : 指定群组;
            unmute_all : 是否解除全体禁言,要求群组参数为必填;
        """
        if target:
            if not group:
                if isinstance(target, Member):
                    group_id = target.group.id
                else:
                    raise ValueError("Missing Argument: group")
            else:
                group_id = group.id if isinstance(group, Group) else group
            await self.communicator.send_handle(
                "unmute",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "target": group_id,
                    "memberId": target.id if isinstance(target, Member) else target
                }
            )
        elif group and unmute_all:
            await self.communicator.send_handle(
                "unmuteAll",
                "POST",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "target": group.id if isinstance(group, Group) else group
                }
            )

    async def kick_member(self, target: Union[Member, int], group: Optional[Union[Group, int]] = None,
                          msg: Optional[str] = ""):
        """
        使用此方法移除指定群成员（需要有相关限权）
        """
        if not group:
            if isinstance(target, Member):
                group_id = target.group.id
            else:
                raise ValueError("Missing Argument: group")
        else:
            group_id = group.id if isinstance(group, Group) else group
        await self.communicator.send_handle(
            "kick",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group_id,
                "memberId": target.id if isinstance(target, Member) else target,
                "msg": msg
            }
        )

    async def self_quit(self, group: Union[Group, int]):
        """
        使用此方法使Bot退出群聊
        """
        await self.communicator.send_handle(
            "quit",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group.id if isinstance(group, Group) else group
            }
        )

    async def set_essence(self, target: Union[Source, BotMessage, int]):
        """
        使用此方法撤回一指定消息
        """
        if isinstance(target, Source):
            target = target.id
        if isinstance(target, BotMessage):
            target = target.messageId

        await self.communicator.send_handle(
            "setEssence",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": target,
            }
        )

    async def get_group_config(self, group: Union[Group, int]):
        result = await self.communicator.send_handle(
            "groupConfig",
            "get",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group.id if isinstance(group, Group) else group
            }
        )

        return GroupConfig.parse_obj(result)

    async def get_member_info(self, member: Union[Member, int], group: Optional[Union[Group, int]] = None):
        if not group and isinstance(member, int):
            raise ValueError("You must give a Member when there isn't Group")
        if isinstance(member, Member) and not group:
            group = member.group
        result = await self.communicator.send_handle(
            "memberInfo",
            "get",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group.id if isinstance(group, Group) else group,
                "memberId": member.id if isinstance(member, Member) else member
            }
        )
        return MemberInfo.parse_obj(result)

    async def get_info(self, target: Union[Group, int, Member]):
        """根据提供的参数自动尝试获取对象的信息或配置

        若想获取群成员信息则target必须为Member

        Args:
            target : 已知的群组或群成员
        """
        if isinstance(target, Member):
            return await self.get_member_info(target)
        return await self.get_group_config(target)

    async def set_group_config(self, group: Union[Group, int], config: GroupConfig):
        await self.communicator.send_handle(
            "groupConfig",
            "update",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group.id if isinstance(group, Group) else group,
                "config": config.dict(exclude_unset=True, exclude_none=True)
            }
        )

    async def set_member_info(self, member: Union[Member, int], member_info: MemberInfo,
                              group: Optional[Union[Group, int]] = None):
        if not group and isinstance(member, int):
            raise ValueError("You must give a Member when there isn't Group")
        if isinstance(member, Member) and not group:
            group = member.group
        await self.communicator.send_handle(
            "memberInfo",
            "update",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group.id if isinstance(group, Group) else group,
                "memberId": member.id if isinstance(member, Member) else member,
                "info": {'name': member_info.name, 'specialTitle': member_info.specialTitle}
            }
        )

    async def modify_admin(self, is_admin: bool, member: Union[Member, int], group: Optional[Union[Group, int]] = None):
        if not group and isinstance(member, int):
            raise ValueError("You must give a Member when there isn't Group")
        if isinstance(member, Member) and not group:
            group = member.group
        await self.communicator.send_handle(
            "memberAdmin",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "target": group.id if isinstance(group, Group) else group,
                "memberId": member.id if isinstance(member, Member) else member,
                "assign": is_admin
            }
        )

    async def upload_image(self, data: bytes, may_method: Optional[str] = None, is_flash: bool = False):
        from .message.element import Image
        from .message.element import FlashImage
        method = may_method or upload_method.get().value
        result = await self.communicator.send_handle(
            "uploadIamge",
            "MULIPART",
            {
                "sessionKey": self.bot_session.sessionKey,
                "type": method,
                "img": data
            }
        )
        if is_flash:
            return FlashImage.parse_obj(result)
        return Image.parse_obj(result)

    async def upload_voice(self, data: bytes, may_method: Optional[str] = None):
        from .message.element import Voice
        method = may_method or upload_method.get().value
        if method == "group":
            result = await self.communicator.send_handle(
                "uploadVoice",
                "MULIPART",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "type": method,
                    "img": data
                }
            )
            return Voice.parse_obj(result)
        else:
            raise TypeError("Voice is only provides sending in group!")

    async def upload_file(self, data: bytes, target: Union[Group, int], may_method: Optional[str] = None,
                          path: str = "", ):
        method = may_method or upload_method.get().value
        if method == "group":
            result = await self.communicator.send_handle(
                "file/upload",
                "MULTIPART",
                {
                    "sessionKey": self.bot_session.sessionKey,
                    "type": method.value,
                    "target": target if isinstance(target, int) else target.id,
                    "path": path,
                    "file": data,
                },
            )
            return FileInfo.parse_obj(result)
        else:
            raise TypeError("File is only provides sending in group!")

    async def file_get_list(self, target: Union[Group, int], dir_id: str = "", with_download_info: bool = False,
                            offset: Optional[int] = 0, size: Optional[int] = 1):
        """
        列出指定文件夹下的所有文件.

        Args:
           target (Union[Group, int]): 目标文件的群号
           dir_id (str): 文件ID, 空串为根目录
           with_download_info (bool): 是否携带下载信息, 无必要不要携带
           offset (int): 分页偏移
           size (int): 分页大小
        Returns:
           FileInfo: 返回的文件信息列表.
        """

        result = await self.communicator.send_handle(
            "file/list",
            "GET",
            {
                "sessionKey": self.bot_session.sessionKey,
                "id": dir_id,
                "target": target.id if isinstance(target, Group) else target,
                "withDownloadInfo": str(with_download_info),
                "offset": offset,
                "size": size
            },
        )

        return [FileInfo.parse_obj(i) for i in result]

    async def file_get_info(self, target: Union[Group, int], dir_id: str = "", with_download_info: bool = False):
        """
        获取指定文件的信息.

        Args:
           target (Union[Group, int]): 目标文件的群号
           dir_id (str): 文件ID, 空串为根目录
           with_download_info (bool): 是否携带下载信息, 无必要不要携带
        Returns:
           FileInfo: 返回的文件信息.
        """

        result = await self.communicator.send_handle(
            "file/list",
            "GET",
            {
                "sessionKey": self.bot_session.sessionKey,
                "id": dir_id,
                "target": target.id if isinstance(target, Group) else target,
                "withDownloadInfo": str(with_download_info)
            },
        )
        return FileInfo.parse_obj(result)

    async def file_make_directory(self, target: Union[Group, int], directory_name: str, dir_id: str = ""):
        """
        在指定位置创建新文件夹.

        Args:
            target (Union[Group, int]): 目标文件的群号
            directory_name (str): 新建文件夹名.
            dir_id (str): 父目录id,空串为根目录
        Returns:
            FileInfo: 新创建文件夹的信息.
        """
        result = await self.communicator.send_handle(
            "file/list",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "id": dir_id,
                "directoryName": directory_name,
                "target": target.id if isinstance(target, Group) else target,
            },
        )
        return FileInfo.parse_obj(result)

    async def file_delete(self, target: Union[Group, int], dir_id: str = ""):
        """
        删除指定文件.

        Args:
           target (Union[Group, int]): 目标文件的群号
           dir_id (str): 删除文件的id
        """
        await self.communicator.send_handle(
            "file/delete",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "id": dir_id,
                "target": target.id if isinstance(target, Group) else target,
            },
        )

    async def file_move(self, target: Union[Group, int], move_to: str, dir_id: str = ""):
        """
        移动指定文件.

        Args:
           target (Union[Group, int]): 目标文件的群号
           move_to (str): 移动目标文件夹的id
           dir_id (str): 移动文件的id
        """
        await self.communicator.send_handle(
            "file/move",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "id": dir_id,
                "target": target.id if isinstance(target, Group) else target,
                "moveTo": move_to
            },
        )

    async def file_rename(self, target: Union[Group, int], rename_to: str, dir_id: str = ""):
        """
        重命名指定文件.

        Args:
           target (Union[Group, int]): 目标文件的群号
           rename_to (str): 新文件名
           dir_id (str): 重命名文件id
        """
        await self.communicator.send_handle(
            "file/rename",
            "POST",
            {
                "sessionKey": self.bot_session.sessionKey,
                "id": dir_id,
                "target": target.id if isinstance(target, Group) else target,
                "renameTO": rename_to
            },
        )
