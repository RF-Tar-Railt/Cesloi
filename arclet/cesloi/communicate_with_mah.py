import asyncio
import inspect
import json
import random
from asyncio import Task

import aiohttp
from typing import Optional, Union, Dict, TYPE_CHECKING, Awaitable, Callable
from aiohttp import ClientSession, WSMsgType
from yarl import URL

from arclet.cesloi.utils import enter_context, Structured
from arclet.letoderea import EventSystem, search_event
from arclet.cesloi.logger import Logger
from .utils import error_check
from .event.base import MiraiEvent

if TYPE_CHECKING:
    from .bot_client import Cesloi


class BotSession(Structured):
    host: str
    single_mode: bool = False
    account: Optional[int] = None
    verifyKey: Optional[str] = None
    sessionKey: Optional[str] = None
    version: Optional[str] = None

    def __init__(
            self,
            host: str,
            account: Optional[int] = None,
            verify_key: Optional[str] = None,
            *,
            single_mode: bool = False,
    ) -> None:
        """
            用于描述与上游接口会话, 并存储会话状态的实体类.

            Args:
                host (AnyHttpUrl): `mirai-api-http` 服务所在的根接口地址
                account (int): 应用所使用账号的整数 ID, singleMode 模式下为空, 非 singleMode 下新建连接不可为空.
                verify_key (str): 配置文件中指定,用以与mah绑定账号
            """
        super().__init__(
            host=host, account=account, verifyKey=verify_key, single_mode=single_mode
        )


class Communicator:
    bot_session: BotSession
    event_system: EventSystem
    loop: asyncio.AbstractEventLoop
    logger: Logger.logger

    def __init__(
            self,
            bot_session: BotSession,
            bot: "Cesloi",
            event_system: EventSystem,
            logger: Optional[Logger] = None
    ):
        self.bot_session = bot_session
        self.event_system = event_system
        self.loop = event_system.loop
        self.logger = logger or Logger().logger
        self.bot = bot
        self.running_task: Optional[Task] = None
        self.running: bool = False
        self.ws_connection: Optional[aiohttp.ClientWebSocketResponse] = None
        self.client_session: Optional[ClientSession] = None
        self.wait_response_future: Dict[str, asyncio.Future] = {}
        self.timeout: float = 30.0

    async def stop(self):
        self.running = False
        if self.running_task and not self.running_task.done():
            try:
                await self.running_task
            except asyncio.CancelledError:
                pass
        self.running_task = None
        self.bot_session.sessionKey = None
        await self.client_session.close()

    @staticmethod
    async def run_always_await(any_callable: Union[Awaitable, Callable]):
        if inspect.isawaitable(any_callable):
            return await any_callable
        else:
            return any_callable

    async def parse_to_event(self, data: dict) -> MiraiEvent:
        """
        从尚未明确指定事件类型的对象中获取事件的定义, 并进行解析

        Args:
            data (dict): 用 dict 表示的序列化态事件, 应包含有字段 `type` 以供分析事件定义.

        Returns:
            MiraiEvent: 已经被序列化的事件
        """
        event_type: Optional[str] = data.get("type")
        if not event_type or not isinstance(event_type, str):
            raise TypeError("Unable to find 'type' field for automatic parsing")
        event_class: Optional[MiraiEvent] = search_event(event_type)
        if not event_class:
            self.logger.error(
                "An event is not recognized! Please report with your log to help us diagnose."
            )
            raise ValueError(f"Unable to find event: {event_type}", data)
        data = {k: v for k, v in data.items() if k != "type"}
        obj = event_class.parse_obj(data)
        return await self.run_always_await(obj)

    async def ws_send_handle(
            self,
            command_name: str, data: Optional[dict] = None, subcommand: Optional[str] = None):
        if not self.bot_session.verifyKey:
            raise ValueError
        sync_id = str(random.randint(0, 100_000_000))
        content = {
            'syncId': sync_id,
            'main': command_name,
            'content': json.dumps(data)
        }
        if subcommand:
            content['subcommand'] = subcommand
        await self.ws_connection.send_json(content)
        future = self.loop.create_future()
        self.wait_response_future[sync_id] = future
        result = await future
        del self.wait_response_future[sync_id]
        del future
        if "data" in result:
            return result['data']
        else:
            return result

    async def send_handle(
            self,
            action: str,
            method: str,
            data: Optional[dict] = None
    ):
        if not self.bot_session.verifyKey:
            raise ValueError
        data = data or dict()
        if method == "GET" or method == "get":
            async with self.client_session.get(
                    URL(f"{self.bot_session.host}/{action}").with_query(data)
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        elif method == "POST" or method == "update":
            async with self.client_session.post(
                    URL(f"{self.bot_session.host}/{action}"), data=json.dumps(data)
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        else:
            form = aiohttp.FormData()
            for k, v in data:
                form.add_fields(k, v)
            async with self.client_session.post(
                    URL(f"{self.bot_session.host}/{action}"), data=form
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        if "data" in response_data:
            resp = response_data['data']
        else:
            resp = response_data
        error_check(response_data)
        return resp

    async def ws_receive_handle(self, unknown_event_data: dict):
        if "syncId" in unknown_event_data:
            data, sync_id = unknown_event_data.get("data"), unknown_event_data.get("syncId")
            if sync_id == "-1":
                event = await self.parse_to_event(data)
                with enter_context(bot=self.bot, event_i=event):
                    self.event_system.event_spread(event)
            else:
                if sync_id not in self.wait_response_future:
                    self.logger.warning(f"syncId {sync_id} not found!")
                else:
                    self.wait_response_future.pop(sync_id).set_result(data)

    async def receive_handle(self, unknown_event_data: dict):
        received_data = unknown_event_data.get('data')
        error_check(received_data)
        event = await self.parse_to_event(received_data)
        with enter_context(bot=self.bot, event_i=event):
            self.event_system.event_spread(event)

    async def websocket(self):
        query = {"qq": self.bot_session.account, "verifyKey": self.bot_session.verifyKey}
        if self.bot_session.single_mode:
            del query['qq']
        async with self.client_session.ws_connect(
                str(URL(self.bot_session.host + "/all").with_query(query)),
                autoping=False,
        ) as connection:
            self.logger.debug("connecting to websocket")
            self.ws_connection = connection
            connected = False
            while self.running:
                try:
                    ws_message = await connection.receive(timeout=self.timeout)
                except asyncio.TimeoutError:
                    try:
                        try:
                            self.logger.debug("websocket: trying ping...")
                            await self.ws_connection.ping()
                        except Exception as e:
                            self.logger.exception(f"websocket: ping failed: {e!r}")
                        else:
                            continue
                    except asyncio.CancelledError:
                        self.logger.warning("websocket: cancelled, stop")
                        return await self.stop()
                if ws_message.type is WSMsgType.TEXT:
                    received_data: dict = json.loads(ws_message.data)
                    if connected:
                        try:
                            await self.receive_handle(received_data)
                        except Exception as e:
                            self.logger.exception(f"receive_data has error {e}")
                    else:
                        if not received_data['syncId']:
                            data = received_data['data']
                            if data['code']:
                                error_check(data)

                            else:
                                if not self.bot_session.sessionKey:
                                    self.bot_session.sessionKey = data.get("session")
                                    connected = True
                elif ws_message.type is WSMsgType.CLOSE:
                    self.logger.info("websocket: server close connection.")
                    return
                elif ws_message.type is WSMsgType.CLOSED:
                    self.logger.info("websocket: connection has been closed.")
                    return
                elif ws_message.type is WSMsgType.PONG:
                    self.logger.debug("websocket: received pong from remote")
                elif ws_message.type == WSMsgType.ERROR:
                    self.logger.warning("websocket: connection error: " + ws_message.data)
                else:
                    self.logger.warning(f"detected a unknown message type: {ws_message.type}")
        self.logger.info("connection disconnected")

    async def connect(self):
        if not self.client_session:
            self.client_session = ClientSession()
        if not self.running_task or self.running_task.done():
            self.running = True
            self.running_task = self.loop.create_task(self.websocket())
