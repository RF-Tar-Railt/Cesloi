import inspect
from typing import Callable, Optional, Union
from pydantic import BaseModel
from inspect import iscoroutinefunction
from cesloi.message.messageChain import MessageChain
from cesloi.command import Command


class SubscriberInterface(BaseModel):
    callable_target: Callable

    class Config:
        arbitrary_types_allowed = True


class Subscriber(SubscriberInterface):
    def __init__(
            self,
            callable_target: Callable,
            subscriber_name: Optional[str] = None,
            command: Optional[Command] = None,
            require_param_name: str = None,
            is_replace_message: bool = True,
            time_schedule: Callable = None,
    ) -> None:
        super().__init__(
            callable_target=callable_target
        )
        self.command = command
        self.subscriber_name = subscriber_name or callable_target.__name__
        self.time_schedule = time_schedule
        self.require_param_name = require_param_name
        self.is_replace_message = is_replace_message
        if not iscoroutinefunction(callable_target):
            raise TypeError("Your Function must be a coroutine function (use async)!")

    def __call__(self, *args, **kwargs):
        return self.callable_target(*args, **kwargs)

    def __repr__(self):
        return f'<Subscriber,name={self.subscriber_name}>'

    def __str__(self):
        return self.__repr__()

    @property
    def name(self):
        return self.subscriber_name

    @name.setter
    def name(self, new_name):
        self.subscriber_name = new_name

    @property
    def params(self):
        return {
            name: [
                param.annotation if param.annotation is not inspect.Signature.empty else None,
                param.default if param.default is not inspect.Signature.empty else None,
            ]
            for name, param in inspect.signature(self.callable_target).parameters.items()
        }

    subscriber_name: Optional[str]
    command: Optional[Command] = None
    time_schedule: Callable = None
    require_param_name: str = None
    is_replace_message: bool = True


class SubscriberHandler:
    """
    订阅器相关的处理器
    """
    subscriber: Subscriber

    def set(
        self,
        subscriber_name: Optional[str] = None,
        command: Command = None,
        require_param_name: str = None,
        is_replace_message: bool = True
        # time_schedule: Callable = None,
    ):
        """该方法生成一个订阅器实例，该订阅器负责调控装饰的可执行函数

        若订阅器的注册事件是消息链相关的，可预先根据写入的命令相关参数进行判别是否执行该订阅器装饰的函数

        若不填如下参数则表示接受任意形式的命令

        Args:
            subscriber_name :装饰器名字，可选
            command :命令处理器，可选
            require_param_name :若命令处理器成功匹配文本并且非完全匹配模式(不含正则表达式)，则根据订阅器下的函数的参数中关于消息链参数的参数名判断是否将匹配到的文本通过该参数传递。
            is_replace_message : 此参数决定是否把匹配的文本传给消息链，默认为True

        """
        def wrapper(func):
            self.subscriber = Subscriber(
                func,
                subscriber_name,
                command,
                require_param_name,
                is_replace_message
                # time_schedule
            )
            return self.subscriber

        return wrapper

    @staticmethod
    def command_handler(sub: Subscriber, msg: Union[str, MessageChain]):
        if isinstance(msg, MessageChain):
            msg = msg.only_text()
        if not sub.command:
            return True, -1
        result = sub.command.analysis(msg)
        if result:
            return True, result

    @staticmethod
    def params_handler(sub: Subscriber, arg: dict, match_msg: str, msg: MessageChain):
        from ...message.element import Plain
        if sub.is_replace_message and match_msg != -1 and not isinstance(match_msg, bool):
            if sub.require_param_name:
                if isinstance(match_msg, str):
                    arg[sub.require_param_name] = msg.replace(Plain, Plain(match_msg), 1)
                if isinstance(match_msg, tuple):
                    arg[sub.require_param_name] = msg.replace(Plain, Plain(",".join(match_msg)), 1)
            else:
                for k, v in arg.items():
                    if v.__class__.__name__ == "MessageChain":
                        if isinstance(match_msg, str):
                            arg[k] = msg.replace(Plain, Plain(match_msg), 1)
                        if isinstance(match_msg, tuple):
                            arg[k] = msg.replace(Plain, Plain(",".join(match_msg)), 1)

        return arg
