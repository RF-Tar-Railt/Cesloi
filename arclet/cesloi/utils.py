import functools
from contextvars import ContextVar
from contextlib import contextmanager
from enum import Enum
from typing import Callable, Any, Union, TYPE_CHECKING
from pydantic.main import BaseModel, BaseConfig, Extra
if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictStrAny, MappingIntStrAny

bot_application = ContextVar("bot_application")
event = ContextVar("event")
event_loop = ContextVar("event_loop")
event_system = ContextVar("event_system")
upload_method = ContextVar("upload_method")


class ContextModel:
    content: Any

    @classmethod
    def set(cls, ct):
        cls.content = ct

    @classmethod
    def get(cls):
        return cls.content

    @classmethod
    def reset(cls, ct):
        cls.content = None
        cls.content = ct


class ContextCollection:
    bot_application: ContextModel
    event: ContextModel
    event_loop: ContextModel
    event_system: ContextModel
    upload_method: ContextModel


class Structured(BaseModel):
    """
    一切数据模型的基类.
    """

    def dict(
        self,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> "DictStrAny":
        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=True,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=True,
        )

    class Config(BaseConfig):
        extra = Extra.allow


class UploadMethods(Enum):
    """用于向 `uploadImage` 或 `uploadVoice` 方法描述图片的上传类型"""

    Friend = "friend"
    Group = "group"
    Temp = "temp"


@contextmanager
def enter_message_send_context(method: UploadMethods):
    t = upload_method.set(method)
    yield
    upload_method.reset(t)


@contextmanager
def enter_context(bot=None, event_i=None):
    t1 = None
    t2 = None
    t3 = None
    t4 = None

    if bot:
        t1 = bot_application.set(bot)
        t3 = event_loop.set(bot.event_system.loop)
        t4 = event_system.set(bot.event_system)
    if event_i:
        t2 = event.set(event_i)

    yield
    try:
        if t1:
            bot_application.reset(t1)

        if all([t2, t3, t4]):
            event.reset(t2)
            event_loop.reset(t3)
            event_system.reset(t4)
    except ValueError:
        pass


def bot_application_context_manager(func: Callable):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        with enter_context(bot=self):
            return await func(self, *args, **kwargs)

    return wrapper
