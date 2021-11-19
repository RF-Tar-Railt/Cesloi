from arclet.cesloi.event.base import MiraiEvent
from arclet.cesloi.message.messageChain import MessageChain
from .inserter import ApplicationInserter, EventInserter
from ..model.relation import Friend


class TestEvent(MiraiEvent):
    type: str = "TestEvent"
    messageChain: MessageChain
    sender: Friend

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            Friend=self.sender
        )