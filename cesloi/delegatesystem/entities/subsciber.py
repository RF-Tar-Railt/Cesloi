import inspect
from typing import Callable, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel
from cesloi.message.messageChain import MessageChain
from cesloi.alconna import Alconna
if TYPE_CHECKING:
    from cesloi.timing.schedule import Toconado


class SubscriberInterface(BaseModel):
    callable_target: Callable

    class Config:
        arbitrary_types_allowed = True


class Subscriber(SubscriberInterface):
    def __init__(
            self,
            callable_target: Callable,
            subscriber_name: Optional[str] = None,
            command: Optional[Alconna] = None,
            time_schedule: Optional["Toconado"] = None,
    ) -> None:
        super().__init__(
            callable_target=callable_target
        )
        self.command = command
        self.subscriber_name = subscriber_name or callable_target.__name__
        self.time_schedule = time_schedule
        # if not iscoroutinefunction(callable_target):
        #    raise TypeError("Your Function must be a coroutine function (use async)!")

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
    command: Optional[Alconna] = None
    time_schedule: Optional["Toconado"] = None


class SubscriberHandler:
    """
    订阅器相关的处理器
    """
    subscriber: Subscriber

    def set(
        self,
        subscriber_name: Optional[str] = None,
        command: Alconna = None,
        time_schedule: "Toconado" = None,
    ):
        """该方法生成一个订阅器实例，该订阅器负责调控装饰的可执行函数

        若订阅器的注册事件是消息链相关的，可预先根据写入的命令相关参数进行判别是否执行该订阅器装饰的函数

        若不填如下参数则表示接受任意形式的命令

        Args:
            subscriber_name :装饰器名字，可选
            command :命令处理器，可选
            time_schedule: 时间调度器，相当于执行间隔，可选
        """
        def wrapper(func):
            self.subscriber = Subscriber(
                func,
                subscriber_name,
                command,
                time_schedule
            )
            return self.subscriber

        return wrapper

    @staticmethod
    def command_handler(sub: Subscriber, msg: Union[str, MessageChain], args: dict):
        if not sub.command or msg == "":
            return args
        result = sub.command.analysis_message(msg)
        for k, v in args.items():
            if v.__class__.__name__ == "Arpamar":
                args[k] = result
                break
        return args

    @staticmethod
    def schedule_handler(sub: Subscriber):
        if not sub.time_schedule:
            return True
        return sub.time_schedule.should_run()
