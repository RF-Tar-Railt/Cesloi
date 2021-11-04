from typing import List, Type, Union

from pydantic import BaseModel

from .event import TemplateEvent
from .subsciber import Subscriber


class PublisherInterface(BaseModel):
    subscribers: List[Subscriber]
    bind_event: Type[TemplateEvent]


class Publisher(PublisherInterface):
    def __init__(
            self,
            *subscriber: List[Subscriber],
            bind_event: Type[TemplateEvent]
    ):
        super().__init__(
            subscribers=list(subscriber),
            bind_event=bind_event
        )

    def subscribers_names(self):
        return [i.name for i in self.subscribers]

    def remove_subscriber(self, target: Union[str, Subscriber]):
        if isinstance(target, Subscriber):
            self.subscribers.pop(self.subscribers.index(target))
        for i in range(0, len(self.subscribers)):
            if self.subscribers[i].name == target:
                self.subscribers.pop(i)
                break

