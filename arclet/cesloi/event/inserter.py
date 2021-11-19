from arclet.letoderea.entities.event import Insertable
from arclet.cesloi.utils import bot_application, event


class ApplicationInserter(Insertable):
    name: str = "bot_application"

    @classmethod
    def get_params(cls):
        return cls.param_export(
            Cesloi=bot_application.get()
        )


class EventInserter(Insertable):
    name: str = "event"

    @classmethod
    def get_params(cls):
        return cls.param_export(
            event=event.get()
        )


if __name__ == "__main__":
    print(EventInserter.get_params())
