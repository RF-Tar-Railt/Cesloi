from typing import Union

from arclet.letoderea.breakpoint import StepOut
from .message.messageChain import MessageChain
from .event.messages import GroupMessage, TempMessage, FriendMessage


def group_message_handler(matched_message: Union[str, MessageChain]):

    class GroupWaiter(StepOut):
        def __init__(self):
            super().__init__(GroupMessage)

        @staticmethod
        def handler(message: MessageChain):
            if isinstance(matched_message, str):
                if message.startswith(matched_message):
                    return message
            elif message.to_text() == matched_message.to_text():
                return message

    return GroupWaiter()


def friend_message_handler(matched_message: Union[str, MessageChain]):

    class FriendWaiter(StepOut):
        def __init__(self):
            super().__init__(FriendMessage)

        @staticmethod
        def handler(message: MessageChain):
            if isinstance(matched_message, str):
                if message.startswith(matched_message):
                    return message
            elif message.to_text() == matched_message.to_text():
                return message

    return FriendWaiter()


def temp_message_handler(matched_message: Union[str, MessageChain]):

    class TempWaiter(StepOut):
        def __init__(self):
            super().__init__(TempMessage)

        @staticmethod
        def handler(message: MessageChain):
            if isinstance(matched_message, str):
                if message.startswith(matched_message):
                    return message
            elif message.to_text() == matched_message.to_text():
                return message

    return TempWaiter()
