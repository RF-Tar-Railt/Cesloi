import asyncio
import json
import random
from asyncio import Task

import aiohttp
from pydantic import BaseModel, AnyHttpUrl, Extra
from typing import Optional, Union, Dict, TYPE_CHECKING
from aiohttp import ClientSession, WSMsgType

from cesloi.context import enter_context
from cesloi.delegatesystem import EventDelegate
from cesloi.logger import Logger
from yarl import URL

if TYPE_CHECKING:
    from .bot_client import Cesloi

code_exceptions_mapping = {
    1: "InvaildAuthkey  错误的verify key",
    2: "AccountNotFound  指定的Bot不存在",
    3: "InvaildSession  Session失效或不存在",
    4: "UnauthorizedSession  Session未认证(未激活)",
    5: "UnknownTarget  发送消息目标不存在(指定对象不存在)",
    6: "FileNotFoundError  指定文件不存在，出现于发送本地图片",
    10: "PermissionError  无操作权限，指Bot没有对应操作的限权",
    20: "AccountMuted  Bot被禁言，指Bot当前无法向指定群发送消息",
    30: "TooLongMessage   	消息过长",
    400: "InvaildArgument  错误的访问，如参数错误等",
}


def error_check(logger, code: Union[dict, int]):
    if isinstance(code, dict):
        code = code.get("code")
        exception_code = code_exceptions_mapping.get(code)
        if exception_code:
            logger.error(exception_code)
    elif isinstance(code, int):
        exception_code = code_exceptions_mapping.get(code)
        if exception_code:
            logger.error(exception_code)


class BotSession(BaseModel):
    host: AnyHttpUrl
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

    class Config:
        allow_mutation = True
        extra = Extra.allow


class Communicator:
    bot_session: BotSession
    delegate: EventDelegate
    loop: asyncio.AbstractEventLoop
    logger: Logger

    def __init__(
            self,
            bot_session: BotSession,
            bot: "Cesloi",
            delegate: EventDelegate,
            logger: Optional[Logger] = None
    ):
        self.bot_session = bot_session
        self.delegate = delegate
        self.loop = delegate.loop
        self.logger = logger or Logger()
        self.bot = bot
        self.running_task: Optional[Task] = None
        self.running: bool = False
        self.ws_connection: Optional[aiohttp.ClientWebSocketResponse] = None
        self.client_session: Optional[ClientSession] = None
        self.wait_response_future: Dict[str, asyncio.Future] = {}

    async def stop(self):
        self.running = False
        if self.running_task and not self.running_task.done():
            try:
                await self.running_task
            except asyncio.CancelledError:
                pass
        self.running_task = None
        self.bot_session.sessionKey = None

    async def ws_send_handle(
            self,
            command_name: str, data: Optional[dict] = None, subcommand: Optional[str] = None):
        if not self.bot_session.verifyKey:
            raise ValueError
        sync_id = str(random.randint(0, 100_000_000))
        content = {
            'syncId': sync_id,
            'command': command_name,
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
        error_check(self.logger, response_data)
        if "data" in response_data:
            return response_data['data']
        else:
            return response_data

    async def ws_receive_handle(self, unknown_event_data: dict):
        if "syncId" in unknown_event_data:
            data, sync_id = unknown_event_data.get("data"), unknown_event_data.get("syncId")
            if sync_id == "-1":
                event = self.delegate.parse_to_event(data)
                with enter_context(bot=self.bot, event_i=event):
                    self.delegate.handle_event(event)
            else:
                if sync_id not in self.wait_response_future:
                    self.logger.warn(f"syncId {sync_id} not found!")
                else:
                    self.wait_response_future.pop(sync_id).set_result(data)

    async def receive_handle(self, unknown_event_data: dict):
        received_data = unknown_event_data.get('data')
        error_check(self.logger, received_data)
        if not self.bot_session.sessionKey:
            if sessionKey := received_data.get("session", None):
                self.bot_session.sessionKey = sessionKey
            return
        event = self.delegate.parse_to_event(received_data)
        with enter_context(bot=self.bot, event_i=event):
            self.delegate.handle_event(event)

    async def websocket(self):
        post_url = f"{self.bot_session.host}/all?" \
                   f"verifyKey={self.bot_session.verifyKey}".replace("http", "ws")
        if not self.bot_session.single_mode:
            post_url += f"&qq={self.bot_session.account}"
        async with self.client_session.ws_connect(
                post_url, autoping=False) as connection:
            self.logger.debug("connecting to" + post_url)
            self.ws_connection = connection
            connected = False
            ping_count = 0
            while self.running:
                try:
                    ws_message = await connection.receive()
                except asyncio.TimeoutError:
                    if ping_count > 5:
                        self.logger.warn("websocket: timeout,stop")
                        await self.stop()
                    else:
                        await self.ws_connection.ping()
                        ping_count += 1
                    continue
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
                                error_check(self.logger, data)
                            else:
                                if not self.bot_session.sessionKey:
                                    if sessionKey := received_data.get("session", None):
                                        self.bot_session.sessionKey = sessionKey
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
                    self.logger.warn("websocket: connection error: " + ws_message.data)
                else:
                    self.logger.warn(f"detected a unknown message type: {ws_message.type}")
        self.logger.info("connection disconnected")

    async def connect(self):
        if not self.client_session:
            self.client_session = ClientSession()
        if not self.running_task or self.running_task.done():
            self.running = True
            self.running_task = self.loop.create_task(self.websocket())
