from cesloi.delegatesystem.entities.paramsInserter import TemplateParamsInserter
from cesloi.context import bot_application, event


class ApplicationInserter(TemplateParamsInserter):
    name: str = "bot_application"

    @classmethod
    def get_param(cls):
        return bot_application.get()


class EventInserter(TemplateParamsInserter):
    name: str = "event"

    @classmethod
    def get_param(cls):
        return event.get()
