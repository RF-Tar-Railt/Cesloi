from typing import Any, Dict, TYPE_CHECKING
from cesloi.delegatesystem.entities.event import ParamsAnalysis, TemplateEvent
if TYPE_CHECKING:
    from ..bot_client import Cesloi


class ApplicationRunning(TemplateEvent):
    bot: "Cesloi"

    def __init__(self, bot):
        super().__init__(bot=bot)

    def get_params(self, params) -> Dict[str, Any]:
        return ParamsAnalysis(

        ).error_param_check(
            params,
            Cesloi=self.bot
        )