import inspect
from typing import Callable, List, Optional, Union
from pydantic import BaseModel
from inspect import iscoroutinefunction
from cesloi.message.messageChain import MessageChain


class SubscriberInterface(BaseModel):
    callable_target: Callable
    command_headers: List[str]
    command_arguments: List[str]


class Subscriber(SubscriberInterface):
    def __init__(
            self,
            callable_target: Callable,
            subscriber_name: Optional[str] = None,
            command_headers: List[str] = None,
            command_arguments: List[str] = None,
            command_separator: Optional[str] = '*',
            time_schedule: Callable = None,
    ) -> None:
        super().__init__(
            callable_target=callable_target,
            command_headers=command_headers or [],
            command_arguments=command_arguments or []
        )
        self.subscriber_name = subscriber_name or callable_target.__name__
        self.time_schedule = time_schedule
        self.command_separator = command_separator
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
    command_separator: Optional[str] = '*'
    time_schedule: Callable = None


class SubscriberHandler:
    """
    订阅器相关的处理器
    """
    subscriber: Subscriber

    def set(
        self,
        subscriber_name: Optional[str] = None,
        command_headers: List[str] = None,
        command_arguments: List[str] = None,
        command_separator: Optional[str] = '*',
        # time_schedule: Callable = None,
    ):
        """该方法生成一个订阅器实例，该订阅器负责调控装饰的可执行函数

        若订阅器的注册事件是消息链相关的，可预先根据写入的命令相关参数进行判别是否执行该订阅器装饰的函数

        若不填如下参数则表示接受任意形式的命令

        Args:
            subscriber_name :装饰器名字，可选
            command_headers :命令头列表，用于判断某命令的头部是否在表中
            command_arguments : 命令参数列表，用于判断某命令的后参数是否在表中
            command_separator : 命令分隔符号，用于解析命令时将命令头与命令参数分隔的指定字符串，默认为“*”
        """
        def wrapper(func):
            self.subscriber = Subscriber(
                func,
                subscriber_name,
                command_headers,
                command_arguments,
                command_separator,
                # time_schedule
            )
            return self.subscriber

        return wrapper

    @staticmethod
    def command_handler(sub: Subscriber, msg: Union[str,MessageChain]):
        if isinstance(msg, MessageChain):
            msg = msg.to_text()
        cmd_part = msg.split(sub.command_separator)
        header = False
        argument = False
        if not sub.command_headers or \
                (sub.command_headers and cmd_part[0] in sub.command_headers):
            header = True
        if not sub.command_arguments:
            argument = True
        if sub.command_arguments and len(cmd_part) > 1:
            for part in cmd_part[1:]:
                if part in sub.command_arguments:
                    argument = True

        return all([header, argument])
