from typing import List, Type

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
