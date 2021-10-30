import functools
from contextvars import ContextVar
from contextlib import contextmanager
from enum import Enum
from typing import Callable

bot_application = ContextVar("bot_application")
event = ContextVar("event")
event_loop = ContextVar("event_loop")
delegate = ContextVar("delegate")
upload_method = ContextVar("upload_method")


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
        t3 = event_loop.set(bot.delegate.loop)
        t4 = delegate.set(bot.delegate)
    if event_i:
        t2 = event.set(event_i)

    yield
    try:
        if t1:
            bot_application.reset(t1)

        if all([t2, t3, t4]):
            event.reset(t2)
            event_loop.reset(t3)
            delegate.reset(t4)
    except ValueError:
        pass


def bot_application_context_manager(func: Callable):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        with enter_context(bot=self):
            return await func(self, *args, **kwargs)

    return wrapper