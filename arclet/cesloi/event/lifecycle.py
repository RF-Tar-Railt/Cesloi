from typing import Any, TYPE_CHECKING
from arclet.letoderea.entities.event import TemplateEvent
if TYPE_CHECKING:
    pass


class ApplicationRunning(TemplateEvent):
    bot: Any

    def __init__(self, bot):
        self.bot = bot

    def get_params(self):
        return self.param_export(
            Cesloi=self.bot
        )


class ApplicationStop(TemplateEvent):
    bot: Any

    def __init__(self, bot):
        self.bot = bot

    def get_params(self):
        return self.param_export(
            Cesloi=self.bot
        )