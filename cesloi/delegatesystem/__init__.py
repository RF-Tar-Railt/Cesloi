import asyncio
import traceback
import time
from typing import List, Union, Type, Dict, Any, Optional
from .entities.event import TemplateEvent
from .entities.publisher import Publisher
from .entities.subsciber import SubscriberHandler


class EventDelegate:
    loop: asyncio.AbstractEventLoop
    publisher_list: List[Publisher]
    safe_interval: float

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None, interval: Optional[float] = None):
        self.loop = loop or asyncio.get_event_loop()
        self.publisher_list = []
        self.safe_interval = interval or 0.001
        self.init_time = time.time()
        self.last_time = self.init_time

    def parse_to_event(self, event_dict: Dict[str, Any]):
        examine_event = self.search_event(event_dict.get('type')).parse_obj(
            {k: v for k, v in event_dict.items() if k != "type"})
        return examine_event

    def handle_event(self, event: TemplateEvent):
        current_time = time.time()
        if current_time - self.last_time > self.safe_interval:
            self.loop.create_task(
                self.exec_subscriber(
                    publisher=self.search_publisher(event.__class__),
                    event=event)
            )
        self.last_time = current_time

    async def exec_subscriber(self, publisher: Publisher, event: TemplateEvent):
        from ..event.messages import Message
        if publisher:
            coroutine = [
                self.get_coroutine_executable_target(
                    target,
                    event.get_params(target.params),  # 执行事件内的参数解析方法，获取可能的函数需要的实际参数
                    message=event.messageChain if isinstance(event, Message) else ""  # 获取可能的消息链
                ) for target in publisher.subscribers
            ]
            results, _ = await asyncio.wait(coroutine)
            for result in results:
                if result.exception() == "PropagationCancelled":
                    break

    @staticmethod
    async def get_coroutine_executable_target(target, real_arguments, message):
        if SubscriberHandler.command_handler(target, message)[0]:  # subscriber的command/time处理
            try:
                result = await target.callable_target(**real_arguments)
            except Exception as e:
                traceback.print_exc()
                raise e
            return result

    def search_publisher(self, event: Type[TemplateEvent]):
        for publisher in self.publisher_list:
            if publisher.bind_event == event:
                return publisher
        return False

    def remove_publisher(self, target):
        self.publisher_list.remove(target)

    @staticmethod
    def event_class_generator(target=TemplateEvent):
        for i in target.__subclasses__():
            yield i
            if i.__subclasses__():
                yield from EventDelegate.event_class_generator(i)

    @staticmethod
    def search_event(name: str):
        for i in EventDelegate.event_class_generator():
            if i.__name__ == name:
                return i

    def register(self, event: Union[str, Type[TemplateEvent]]):
        if isinstance(event, str):
            name = event
            event = self.search_event(event)
            if not event:
                raise Exception(name + " cannot found!")

        def register_wrapper(subscriber):
            temp_publisher = self.search_publisher(event)
            if not temp_publisher:
                self.publisher_list.append(Publisher(subscriber, bind_event=event))
            else:
                if subscriber.name not in temp_publisher.subscribers_names():
                    temp_publisher.subscribers.append(subscriber)
                else:
                    raise ValueError(f"Function \"{subscriber.name}\" for {event.__name__} has already registered!")
            return subscriber

        return register_wrapper
