from cesloi.event.base import MiraiEvent
from cesloi.delegatesystem.entities.event import ParamsAnalysis
from cesloi.message.messageChain import MessageChain
from .inserter import ApplicationInserter, EventInserter
from ..message import Friend


class TestEvent(MiraiEvent):
    type: str = "TestEvent"
    messageChain: MessageChain
    sender: Friend

    def get_params(self, params):
        return ParamsAnalysis(
            ApplicationInserter,
            EventInserter
        ).error_param_check(
            params,
            MessageChain=self.messageChain,
            Friend=self.sender
        )