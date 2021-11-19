from typing import Union
from .base import MiraiEvent
from arclet.cesloi.model.relation import Client, Friend, Member
from arclet.cesloi.message.messageChain import MessageChain
from .inserter import ApplicationInserter, EventInserter


class Message(MiraiEvent):
    type: str
    messageChain: MessageChain
    sender: Union[Friend, Member, Client]

    def __eq__(self, other: "Message"):
        return self.messageChain.to_text() == other

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            sender=self.sender
        )


class FriendMessage(Message):
    type: str = "FriendMessage"
    sender: Friend

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            Friend=self.sender
        )


class GroupMessage(Message):
    type: str = "GroupMessage"
    sender: Member

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            Member=self.sender,
            Group=self.sender.group
        )


class TempMessage(Message):
    type: str = "TempMessage"
    sender: Member

    def get_params(self,):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            Member=self.sender,
            Group=self.sender.group
        )


class StrangerMessage(Message):
    type: str = "StrangerMessage"
    sender: Friend

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            Friend=self.sender
        )


class OtherClientMessage(Message):
    type: str = "OtherClientMessage"
    sender: Client

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter,
            MessageChain=self.messageChain,
            Client=self.sender
        )